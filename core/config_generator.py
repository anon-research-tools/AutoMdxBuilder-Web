"""
配置文件生成器
用于生成 AutoMdxBuilder 所需的 build.toml 配置文件
"""
import toml
from pathlib import Path


class BuildTomlGenerator:
    """生成 build.toml 配置文件"""

    def __init__(self, template_choice):
        """
        初始化配置生成器

        Args:
            template_choice: 模板选择 'A', 'B', 'C', 或 'D'
        """
        self.template = template_choice.upper()
        self.config = {
            'global': {},
            'template': {
                'a': {},
                'b': {},
                'c': {},
                'd': {}
            }
        }

    def set_global_config(self, name, name_abbr, simp_trad_flg=False):
        """
        设置全局配置

        Args:
            name: 词典名称
            name_abbr: 词典缩写
            simp_trad_flg: 是否启用繁简转换
        """
        self.config['global'] = {
            'templ_choice': self.template,
            'name': name,
            'name_abbr': name_abbr,
            'simp_trad_flg': simp_trad_flg
        }

    def set_template_a_config(self, body_start, navi_items=None):
        """
        设置模板 A 配置

        Args:
            body_start: 正文起始页码
            navi_items: 导航项列表 (可选)
        """
        self.config['template']['a']['body_start'] = body_start
        if navi_items:
            self.config['template']['a']['navi_items'] = navi_items

    def set_template_b_config(self, body_start):
        """
        设置模板 B 配置

        Args:
            body_start: 正文起始页码
        """
        self.config['template']['b']['body_start'] = body_start

    def set_template_c_config(self):
        """设置模板 C 配置（文本词典，无特殊配置）"""
        pass

    def set_template_d_config(self):
        """设置模板 D 配置（文本词典，无特殊配置）"""
        pass

    def generate(self, output_path):
        """
        生成 build.toml 文件

        Args:
            output_path: 输出目录路径

        Returns:
            Path: 生成的配置文件路径
        """
        output_file = Path(output_path) / 'build.toml'

        with open(output_file, 'w', encoding='utf-8') as f:
            toml.dump(self.config, f)

        return output_file

    def validate(self):
        """
        验证配置有效性

        Returns:
            tuple: (is_valid, error_message)
        """
        # 检查全局配置
        if not self.config['global'].get('name'):
            return False, "项目名称不能为空"

        if not self.config['global'].get('name_abbr'):
            return False, "项目缩写不能为空"

        # 检查模板特定配置
        template_key = self.template.lower()

        if self.template in ['A', 'B']:
            # 图像词典需要 body_start
            if 'body_start' not in self.config['template'][template_key]:
                return False, f"模板 {self.template} 需要设置正文起始页"

            body_start = self.config['template'][template_key]['body_start']
            if not isinstance(body_start, int) or body_start < 1:
                return False, "正文起始页必须是大于0的整数"

        return True, ""


def create_config_from_dict(config_dict):
    """
    从字典创建配置文件

    Args:
        config_dict: 包含所有配置的字典
            {
                'name': '词典名称',
                'abbr': '缩写',
                'template': 'B',
                'body_start': 62,
                'simp_trad': True,
                ...
            }

    Returns:
        BuildTomlGenerator: 配置好的生成器实例
    """
    generator = BuildTomlGenerator(config_dict['template'])

    # 设置全局配置
    generator.set_global_config(
        name=config_dict['name'],
        name_abbr=config_dict.get('abbr', config_dict['name'][:6].upper()),
        simp_trad_flg=config_dict.get('simp_trad', False)
    )

    # 根据模板设置特定配置
    template = config_dict['template'].upper()

    if template == 'A':
        generator.set_template_a_config(
            body_start=config_dict.get('body_start', 1),
            navi_items=config_dict.get('navi_items')
        )
    elif template == 'B':
        generator.set_template_b_config(
            body_start=config_dict.get('body_start', 1)
        )
    elif template == 'C':
        generator.set_template_c_config()
    elif template == 'D':
        generator.set_template_d_config()

    return generator
