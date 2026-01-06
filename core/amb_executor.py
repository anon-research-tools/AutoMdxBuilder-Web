"""
AutoMdxBuilder 执行器 (Web版本)
调用 AutoMdxBuilder 可执行文件制作词典
"""
import subprocess
import os
import signal
import time
from pathlib import Path
from utils.logger import get_logger

logger = get_logger()


class AutoMdxBuilderExecutor:
    """AutoMdxBuilder 执行器"""

    def __init__(self, amb_path):
        """
        初始化执行器

        Args:
            amb_path: AutoMdxBuilder 可执行文件路径
        """
        self.amb_path = Path(amb_path)
        self.process = None

    def execute(self, config_path, output_callback=None, timeout=3600):
        """
        执行 AutoMdxBuilder

        Args:
            config_path: 配置文件路径 (build.toml/config.toml)
            output_callback: 输出回调函数 callback(line)
            timeout: 超时时间（秒），默认 1 小时

        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            # 检查 AutoMdxBuilder 是否存在
            if not self.amb_path.exists():
                error_msg = f"找不到 AutoMdxBuilder: {self.amb_path}"
                logger.error(error_msg)
                return False, error_msg

            # 获取项目目录
            project_dir = Path(config_path).parent
            if not project_dir.exists():
                error_msg = f"项目目录不存在: {project_dir}"
                logger.error(error_msg)
                return False, error_msg

            # 检查配置文件
            if not Path(config_path).exists():
                error_msg = f"配置文件不存在: {config_path}"
                logger.error(error_msg)
                return False, error_msg

            logger.info(f"项目目录: {project_dir}")
            logger.info(f"配置文件: {config_path}")
            logger.info(f"AutoMdxBuilder: {self.amb_path}")

            if output_callback:
                output_callback(f"项目目录: {project_dir}")
                output_callback(f"配置文件: {config_path}")
                output_callback(f"开始制作词典...")

            # 设置工作目录为 AutoMdxBuilder 所在目录
            # 这样它可以找到 lib/ 等资源文件
            amb_dir = Path(self.amb_path).parent
            cwd = str(amb_dir)

            # 构建命令
            cmd = [str(self.amb_path)]
            
            # 在 Linux 下使用 nice 降低优先级，防止 CPU 抢占
            import sys
            if sys.platform != 'win32':
                cmd = ['nice', '-n', '10'] + cmd

            logger.info(f"执行命令: {' '.join(cmd)}")
            logger.info(f"工作目录: {cwd}")

            # 启动子进程
            # 使用 start_new_session 可以在停止时更好地清理进程树
            self.process = subprocess.Popen(
                cmd,
                cwd=cwd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                start_new_session=True
            )

            # 实时读取输出，增加超时检查
            start_time = time.time()
            options_sent = False
            dir_sent = False
            
            # 使用更健壮的读取方式，不依赖于换行符
            # 因为提示符可能没有换行
            
            output_buffer = ""
            
            while True:
                # 检查是否超时
                if time.time() - start_time > timeout:
                    logger.error("AutoMdxBuilder 执行超时")
                    self.stop()
                    return False, "执行超时"

                # 检查进程是否已结束
                poll = self.process.poll()
                if poll is not None:
                    # 读取剩余输出
                    remaining = self.process.stdout.read()
                    if remaining:
                        for l in remaining.splitlines():
                            if l.strip():
                                logger.info(f"AutoMdxBuilder: {l}")
                                if output_callback:
                                    output_callback(l)
                    break

                # 交互逻辑：发送指令
                # 尝试读取一些字符
                char = self.process.stdout.read(1)
                if char:
                    output_buffer += char
                    if char == '\n' or any(kw in output_buffer for kw in ["数字", "目录", "Directory", "Path", "指定", "路径"]):
                        line = output_buffer.strip()
                        if line:
                            logger.info(f"AutoMdxBuilder: {line}")
                            if output_callback:
                                output_callback(line)
                            
                            # 自动交互
                            if not options_sent and any(kw in line for kw in ["选择", "Select", "20", "输入数字", "数字"]):
                                logger.info("响应：发送 20")
                                try:
                                    self.process.stdin.write("20\n")
                                    self.process.stdin.flush()
                                    options_sent = True
                                except BrokenPipeError:
                                    logger.warning("发送 20 时 Pipe 已关闭")
                                
                            elif options_sent and not dir_sent and any(kw in line for kw in ["目录", "Directory", "Path", "指定", "路径"]):
                                logger.info(f"响应：发送 {config_path}")
                                try:
                                    self.process.stdin.write(f"{config_path}\n")
                                    self.process.stdin.flush()
                                    dir_sent = True
                                except BrokenPipeError:
                                    logger.warning(f"发送 {config_path} 时 Pipe 已关闭")
                            
                            elif options_sent and dir_sent and any(kw in line for kw in ["恭喜", "生成", "完毕"]):
                                logger.info("响应：发送回车退出")
                                try:
                                    self.process.stdin.write("\n")
                                    self.process.stdin.flush()
                                except BrokenPipeError:
                                    pass # 已经关闭是正常的
                        
                        output_buffer = "" if char == '\n' else output_buffer
                else:
                    time.sleep(0.1)

            # 等待进程结束
            return_code = self.process.wait()
            logger.info(f"AutoMdxBuilder进程结束，返回码: {return_code}")

            if return_code == 0:
                # 查找生成的 MDX 文件
                # AutoMdxBuilder 可能会把文件放在子目录中（例如 XXX_mdict）
                mdx_files = list(project_dir.rglob("*.mdx"))
                mdd_files = list(project_dir.rglob("*.mdd"))

                logger.info(f"生成了 {len(mdx_files)} 个MDX文件，{len(mdd_files)} 个MDD文件")

                if not mdx_files:
                    return False, "制作完成但未找到生成的 MDX 文件"

                result_msg = "词典制作成功!\n\n生成的文件:\n"
                for mdx in mdx_files:
                    size_mb = mdx.stat().st_size / (1024 * 1024)
                    result_msg += f"• {mdx.name} ({size_mb:.1f} MB)\n"
                    logger.info(f"  - {mdx.name} ({size_mb:.1f} MB)")
                for mdd in mdd_files:
                    size_mb = mdd.stat().st_size / (1024 * 1024)
                    result_msg += f"• {mdd.name} ({size_mb:.1f} MB)\n"
                    logger.info(f"  - {mdd.name} ({size_mb:.1f} MB)")

                return True, result_msg
            else:
                error_msg = f"制作失败 (返回码: {return_code})"
                logger.error(error_msg)
                return False, error_msg

        except Exception as e:
            error_msg = f"执行错误: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return False, error_msg

    def stop(self):
        """停止执行"""
        if self.process:
            try:
                # 尝试优雅停止进程组
                os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
                    self.process.wait(timeout=2)
            except Exception as e:
                logger.error(f"停止进程时出错: {e}", exc_info=True)
            finally:
                self.process = None
