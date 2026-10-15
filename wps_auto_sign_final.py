#!/usr/bin/env python3
"""
WPS自动签到脚本 - 最终版（使用JS点击）
"""

import time``
import logging
import os
import sys
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

# ========== 配置区 ==========
SIGN_PAGE_URL = 'https://personal-act.wps.cn/rubik2/portal/HD2025031821201822/YM2025031821202008?cs_from=web_vipcenter_banner_onsale_inpublic&mk_key=1iphykKzNVLR8QSL3tqEBEKioz5GiV3JV9oa9Qmloe&position=pc_aty_banunion_ungrade_test_a_pc_web_hd'

MY_COOKIES = [
   {'name': 'wps_sid', 'value': 'V02SFed0s7WtDm0WVequlHGF0-bNwgY00aeaae94000db7b8cb', 'domain': '.wps.cn'},
    {'name': 'kso_sid', 'value': 'TKS-f0fbcN8k009AGVvA0poTTKS7fKoAKQKSrx5D4rKjz7oWTRvxemB7fe0odC5uO7ZDN7oqA9UwOfI937SA6SruKoff4lem2KnG9OJhs6WadDiXSrkwR86mYzp9s2IFJQr0S7STqN9xsJqZ-8ESz1osGRxFBj6AFGTq0zeHgTgjLT2_v_aKCvLj5KuIKcIKWrIIKQ.0xLU-o9KM3rjif6fFmScQTOmgQgOxAflpunYVUtcWWLXn77n9t8m4fa1iagj51GptGdlEie3h_3Zqm-a7yJmpQ', 'domain': '.wps.cn'},
    {'name': 'uid', 'value': '230144203', 'domain': '.wps.cn'},
    {'name': 'csrf', 'value': '4knSpBFitRz6CTCJywkQ6A38Jz6x5Ww2', 'domain': '.wps.cn'},
]

# XPath选择器
SIGN_BUTTON_XPATH = "//div[contains(@class, 'sign-opera-btn')]"

# ========== 日志设置 ==========
log_dir = '/tmp/wps_logs'
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler(f'{log_dir}/wps_sign.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def setup_driver():
    """配置并返回无头Chrome驱动"""
    options = webdriver.ChromeOptions()
    
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--remote-debugging-port=9222')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-blink-features=AutomationControlled')
    
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    try:
        driver = webdriver.Chrome(options=options)
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": "Object.defineProperty(navigator, 'webdriver', { get: () => undefined });"
        })
        logger.info("无头Chrome浏览器启动成功")
        return driver
    except Exception as e:
        logger.error(f"启动浏览器失败: {e}")
        raise

def add_cookies_to_driver(driver, target_url):
    """将Cookie注入浏览器"""
    try:
        logger.info("开始注入Cookie...")
        
        driver.get('https://personal-act.wps.cn')
        time.sleep(2)
        
        for cookie_dict in MY_COOKIES:
            try:
                driver.add_cookie(cookie_dict)
                logger.debug(f"添加Cookie: {cookie_dict['name']}")
            except Exception as e:
                logger.warning(f"添加Cookie {cookie_dict['name']} 时出错: {e}")
        
        driver.get(target_url)
        time.sleep(3)
        logger.info("Cookie注入完成，页面加载成功")
        return True
        
    except Exception as e:
        logger.error(f"注入Cookie失败: {e}")
        return False

def find_all_buttons(driver):
    """查找所有可能的签到按钮"""
    try:
        buttons = driver.find_elements(By.XPATH, SIGN_BUTTON_XPATH)
        logger.info(f"找到 {len(buttons)} 个签到按钮")
        
        for i, btn in enumerate(buttons):
            text = btn.text.strip()
            disabled_attr = btn.get_attribute('disabled')
            html = btn.get_attribute('outerHTML')[:100]  # 前100个字符
            logger.info(f"按钮{i+1}: 文本='{text}', disabled属性={disabled_attr}")
            logger.debug(f"按钮{i+1} HTML: {html}")
        
        return buttons
    except Exception as e:
        logger.error(f"查找按钮失败: {e}")
        return []

def click_with_js(driver, button):
    """使用JavaScript点击按钮（绕过disabled限制）"""
    try:
        logger.info("使用JavaScript点击按钮...")
        
        # 点击前截图
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        driver.save_screenshot(f'{log_dir}/js_before_click_{timestamp}.png')
        
        # 使用JavaScript点击
        driver.execute_script("arguments[0].click();", button)
        logger.info("✅ JavaScript点击执行完成")
        
        # 等待响应
        time.sleep(3)
        
        # 点击后截图
        driver.save_screenshot(f'{log_dir}/js_after_click_{timestamp}.png')
        
        return True
    except Exception as e:
        logger.error(f"JavaScript点击失败: {e}")
        return False

def check_and_click_sign_button(driver):
    """检查按钮状态并点击"""
    try:
        # 查找所有按钮
        buttons = find_all_buttons(driver)
        if not buttons:
            logger.error("❌ 未找到任何签到按钮")
            return False
        
        # 分析按钮状态
        for i, button in enumerate(buttons):
            text = button.text.strip()
            
            # 如果已经签到
            if "已签到" in text:
                logger.info("✅ 今天已经签到过了")
                return True
            
            # 如果是签到按钮（无论disabled状态）
            if "点击签到" in text or "签到" in text:
                logger.info(f"找到签到按钮（按钮{i+1}），尝试点击...")
                
                # 先尝试正常点击
                try:
                    logger.info("尝试正常点击...")
                    button.click()
                    logger.info("✅ 正常点击成功")
                    time.sleep(3)
                    return True
                except Exception as e:
                    logger.warning(f"正常点击失败: {e}")
                    logger.info("尝试JavaScript点击...")
                    
                    # 如果正常点击失败，使用JavaScript点击
                    if click_with_js(driver, button):
                        return True
        
        logger.warning("没有找到可点击的签到按钮")
        return False
                
    except Exception as e:
        logger.error(f"处理按钮时出错: {e}")
        return False

def main():
    """主函数"""
    logger.info("="*50)
    logger.info(f"WPS自动签到开始 @ {datetime.now()}")
    logger.info("="*50)
    
    driver = None
    try:
        # 1. 启动浏览器
        logger.info("步骤1: 启动无头Chrome浏览器...")
        driver = setup_driver()
        
        # 2. 注入Cookie并访问页面
        logger.info("步骤2: 注入Cookie并访问签到页面...")
        if not add_cookies_to_driver(driver, SIGN_PAGE_URL):
            logger.error("Cookie注入失败，终止")
            return False
        
        # 3. 检查并点击签到按钮
        logger.info("步骤3: 检查签到按钮状态...")
        success = check_and_click_sign_button(driver)
        
        if success:
            logger.info("🎉 自动签到流程执行成功！")
        else:
            logger.warning("⚠️ 签到流程执行中遇到问题")
        
        return success
        
    except WebDriverException as e:
        logger.error(f"🚨 浏览器驱动异常: {e}")
        return False
    except Exception as e:
        logger.error(f"🚨 发生未捕获异常: {e}")
        return False
    finally:
        if driver:
            driver.quit()
            logger.info("浏览器已关闭")
        logger.info(f"任务结束 @ {datetime.now()}")
        logger.info("="*50)

if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    exit_code = 0 if main() else 1
    sys.exit(exit_code)
