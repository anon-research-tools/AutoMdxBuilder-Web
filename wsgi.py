"""
WSGI入口文件
"""
import os
from dotenv import load_dotenv
from app import create_app

# 加载配置
load_dotenv()

# 从环境变量获取配置
config_name = os.environ.get('FLASK_ENV', 'production')
app = create_app(config_name)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=False)
