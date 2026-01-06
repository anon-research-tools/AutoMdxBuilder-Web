"""
PDF 处理器
用于处理 PDF 文件，包括转换为图片、提取书签等
"""
import fitz  # PyMuPDF
import gc
import os
from pathlib import Path
from PIL import Image, ImageOps
from typing import Callable, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from multiprocessing import cpu_count
from utils.logger import get_logger

logger = get_logger()


class PDFProcessor:
    """PDF 处理工具"""

    def __init__(self, pdf_path):
        """
        初始化 PDF 处理器

        Args:
            pdf_path: PDF 文件路径
        """
        self.pdf_path = Path(pdf_path)
        try:
            self.doc = fitz.open(str(self.pdf_path))
            logger.info(f"成功打开PDF文件: {self.pdf_path}")
        except Exception as e:
            logger.error(f"无法打开PDF文件 {self.pdf_path}: {e}", exc_info=True)
            raise

    def get_page_count(self):
        """
        获取 PDF 页数

        Returns:
            int: 页数
        """
        return len(self.doc)

    def get_page_preview(self, page_num, max_size=(300, 400)):
        """
        获取页面预览图

        Args:
            page_num: 页码 (0-based)
            max_size: 最大尺寸 (width, height)

        Returns:
            PIL.Image: 预览图
        """
        if page_num < 0 or page_num >= len(self.doc):
            raise ValueError(f"页码超出范围: {page_num}")

        page = self.doc[page_num]
        pix = page.get_pixmap()

        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        img.thumbnail(max_size, Image.Resampling.LANCZOS)

        return img

    def extract_images(self, output_dir, dpi=200, crop=True,
                      quality=75, progress_callback: Optional[Callable] = None,
                      parallel=True, num_workers=None):
        """
        提取 PDF 所有页面为图片（支持多进程并行）

        Args:
            output_dir: 输出目录
            dpi: 分辨率 (默认 200)
            crop: 是否裁剪空白边距 (默认 True)
            quality: 图片质量 1-100 (默认 75)
            progress_callback: 进度回调函数 callback(current, total, page_num)
            parallel: 是否使用多进程并行处理 (默认 True)
            num_workers: 工作进程数 (默认为CPU核心数)

        Returns:
            dict: 转换结果统计
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        total_pages = self.get_page_count()

        # 决定是否使用并行处理
        # 页数少于20页时，单线程可能更快（避免进程启动开销）
        use_parallel = parallel and total_pages >= 20

        if use_parallel:
            logger.info(f"开始转换PDF（多进程并行），共 {total_pages} 页，DPI={dpi}, 裁剪={crop}")
            return self._extract_images_parallel(
                output_path, dpi, crop, quality,
                progress_callback, num_workers
            )
        else:
            logger.info(f"开始转换PDF（单进程），共 {total_pages} 页，DPI={dpi}, 裁剪={crop}")
            return self._extract_images_sequential(
                output_path, dpi, crop, quality,
                progress_callback
            )

    def _extract_images_sequential(self, output_path, dpi, crop, quality, progress_callback):
        """单进程顺序处理（原有逻辑）"""
        total_pages = self.get_page_count()
        successful_pages = 0

        for page_num in range(total_pages):
            try:
                page = self.doc[page_num]

                # 设置缩放比例 (DPI)
                zoom = dpi / 72
                mat = fitz.Matrix(zoom, zoom)

                # 渲染页面
                pix = page.get_pixmap(matrix=mat)

                # 转换为 PIL Image
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

                # 释放pixmap内存
                pix = None

                # 裁剪空白边距
                if crop:
                    try:
                        img = self.crop_whitespace(img, margin=10)
                    except Exception as e:
                        logger.warning(f"页面 {page_num + 1} 裁剪失败: {e}")

                # 保存图片
                img_path = output_path / f"{page_num + 1:04d}.png"
                img.save(img_path, "PNG", optimize=True)

                # 释放图片内存
                img.close()
                img = None

                successful_pages += 1

                # 进度回调
                if progress_callback:
                    progress_callback(page_num + 1, total_pages, page_num + 1)

                # 每10页强制垃圾回收一次
                if (page_num + 1) % 10 == 0:
                    gc.collect()

            except Exception as e:
                logger.error(f"转换页面 {page_num + 1} 时出错: {e}", exc_info=True)

        logger.info(f"PDF转换完成，成功转换 {successful_pages}/{total_pages} 页")
        return {
            'successful': successful_pages,
            'failed': total_pages - successful_pages,
            'total': total_pages
        }

    def _extract_images_parallel(self, output_path, dpi, crop, quality, progress_callback, num_workers):
        """多线程并行处理（使用ThreadPoolExecutor）"""
        total_pages = self.get_page_count()

        # 确定工作线程数
        if num_workers is None:
            num_workers = min(cpu_count(), 12)  # 限制为物理核心数，避免 CPU 过载

        logger.info(f"使用 {num_workers} 个工作线程进行并行处理")

        # 准备任务参数
        tasks = [
            (str(self.pdf_path), page_num, str(output_path), dpi, crop, quality)
            for page_num in range(total_pages)
        ]

        # 使用线程池并行处理
        successful_pages = 0
        processed = 0

        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            # 提交所有任务
            future_to_page = {
                executor.submit(_process_single_page, task): task[1]
                for task in tasks
            }

            # 处理完成的任务
            for future in as_completed(future_to_page):
                processed += 1
                try:
                    result = future.result()
                    if result:
                        successful_pages += 1
                except Exception as e:
                    logger.error(f"任务处理异常: {e}")

                # 进度回调
                if progress_callback:
                    progress_callback(processed, total_pages, processed)

                # 定期垃圾回收
                if processed % 20 == 0:
                    gc.collect()

        failed_pages = total_pages - successful_pages
        logger.info(f"PDF转换完成，成功转换 {successful_pages}/{total_pages} 页")

        return {
            'successful': successful_pages,
            'failed': failed_pages,
            'total': total_pages
        }

    def crop_whitespace(self, img, margin=10):
        """
        裁剪图片空白边距

        Args:
            img: PIL Image 对象
            margin: 保留的边距像素数 (默认 10)

        Returns:
            PIL.Image: 裁剪后的图片
        """
        # 转换为灰度
        gray = img.convert('L')

        # 反转颜色 (白色 -> 黑色)
        inverted = ImageOps.invert(gray)

        # 获取边界框
        bbox = inverted.getbbox()

        if bbox:
            # 添加边距
            bbox = (
                max(0, bbox[0] - margin),
                max(0, bbox[1] - margin),
                min(img.width, bbox[2] + margin),
                min(img.height, bbox[3] + margin)
            )
            return img.crop(bbox)

        return img

    def extract_bookmarks(self):
        """
        提取 PDF 书签

        Returns:
            list: 书签列表
                [
                    {'level': 0, 'title': '第一章', 'page': 10},
                    {'level': 1, 'title': '第一节', 'page': 12},
                    ...
                ]
        """
        toc = self.doc.get_toc()

        bookmarks = []
        for item in toc:
            level, title, page = item
            bookmarks.append({
                'level': level - 1,  # 转换为 0-based
                'title': title,
                'page': page
            })

        return bookmarks

    def has_bookmarks(self):
        """
        检查 PDF 是否包含书签

        Returns:
            bool: 是否有书签
        """
        return len(self.doc.get_toc()) > 0

    def close(self):
        """关闭 PDF 文档并释放资源"""
        if self.doc:
            try:
                self.doc.close()
                logger.debug(f"已关闭PDF文档: {self.pdf_path}")
            except Exception as e:
                logger.warning(f"关闭PDF文档时出错: {e}")
            finally:
                self.doc = None
                gc.collect()

    def __enter__(self):
        """支持 with 语句"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """支持 with 语句"""
        self.close()

    def __del__(self):
        """析构函数，确保文档被关闭"""
        self.close()


def _process_single_page(args):
    """
    处理单个PDF页面（供多进程调用）

    Args:
        args: (pdf_path, page_num, output_path, dpi, crop, quality)

    Returns:
        bool: 是否成功
    """
    pdf_path, page_num, output_path, dpi, crop, quality = args

    try:
        # 每个进程打开自己的PDF文档
        doc = fitz.open(pdf_path)
        page = doc[page_num]

        # 设置缩放比例
        zoom = dpi / 72
        mat = fitz.Matrix(zoom, zoom)

        # 渲染页面
        pix = page.get_pixmap(matrix=mat)

        # 转换为 PIL Image
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        # 释放pixmap内存
        pix = None

        # 裁剪空白边距
        if crop:
            try:
                img = _crop_whitespace_standalone(img, margin=10)
            except Exception:
                pass  # 裁剪失败则跳过

        # 保存图片
        output_file = Path(output_path) / f"{page_num + 1:04d}.png"
        img.save(output_file, "PNG", optimize=True)

        # 清理资源
        img.close()
        doc.close()
        gc.collect()

        return True

    except Exception as e:
        logger.error(f"处理页面 {page_num + 1} 失败: {e}")
        return False


def _crop_whitespace_standalone(img, margin=10):
    """独立的裁剪函数（供多进程调用）"""
    gray = img.convert('L')
    inverted = ImageOps.invert(gray)
    bbox = inverted.getbbox()

    if bbox:
        bbox = (
            max(0, bbox[0] - margin),
            max(0, bbox[1] - margin),
            min(img.width, bbox[2] + margin),
            min(img.height, bbox[3] + margin)
        )
        return img.crop(bbox)

    return img


def convert_pdf_to_images(pdf_path, output_dir, dpi=200, crop=True,
                          progress_callback=None, parallel=True):
    """
    便捷函数：将 PDF 转换为图片

    Args:
        pdf_path: PDF 文件路径
        output_dir: 输出目录
        dpi: 分辨率
        crop: 是否裁剪空白
        progress_callback: 进度回调
        parallel: 是否使用并行处理

    Returns:
        dict: 转换结果统计
    """
    with PDFProcessor(pdf_path) as processor:
        return processor.extract_images(
            output_dir=output_dir,
            dpi=dpi,
            crop=crop,
            progress_callback=progress_callback,
            parallel=parallel
        )
