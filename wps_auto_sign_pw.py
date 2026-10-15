import os
import sys
import logging
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)

SIGN_PAGE_URL = (
    "https://personal-act.wps.cn/rubik2/portal/HD2025031821201822/"
    "YM2025031821202008"
    "?cs_from=web_vipcenter_banner_onsale_inpublic"
    "&mk_key=1iphykKzNVLR8QSL3tqEBEKioz5GiV3JV9oa9Qmloe"
    "&position=pc_aty_banunion_ungrade_test_a_pc_web_hd"
)

MY_COOKIES = [
    {"name": "wps_sid", "value": "V02SFed0s7WtDm0WVequlHGF0-bNwgY00aeaae94000db7b8cb", "domain": ".wps.cn", "path": "/"},
    {"name": "kso_sid", "value": "TKS-f0fbcN8k009AGVvA0poTTKS7fKoAKQKSrx5D4rKjz7oWTRvxemB7fe0odC5uO7ZDN7oqA9UwOfI937SA6SruKoff4lem2KnG9OJhs6WadDiXSrkwR86mYzp9s2IFJQr0S7STqN9xsJqZ-8ESz1osGRxFBj6AFGTq0zeHgTgjLT2_v_aKCvLj5KuIKcIKWrIIKQ.0xLU-o9KM3rjif6fFmScQTOmgQgOxAflpunYVUtcWWLXn77n9t8m4fa1iagj51GptGdlEie3h_3Zqm-a7yJmpQ", "domain": ".wps.cn", "path": "/"},
    {"name": "uid", "value": "230144203", "domain": ".wps.cn", "path": "/"},
    {"name": "csrf", "value": "4knSpBFitRz6CTCJywkQ6A38Jz6x5Ww2", "domain": ".wps.cn", "path": "/"},
]

def main():
    logger.info("WPS自动签到开始")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
            ],
        )
        context = browser.new_context()
        context.add_cookies(MY_COOKIES)
        page = context.new_page()

        try:
            page.goto(SIGN_PAGE_URL, timeout=30000, wait_until="domcontentloaded")
            page.wait_for_timeout(3000)

            sign_btn = page.locator("div.sign-opera-btn, text=签到").first

            if sign_btn.count() == 0:
                logger.info("未找到签到按钮，可能已签到或页面结构变化")
                return

            text = (sign_btn.text_content() or "").strip()
            if "已签到" in text:
                logger.info("今天已经签到过了")
                return

            logger.info("点击签到按钮")
            sign_btn.click(timeout=10000)
            page.wait_for_timeout(3000)
            logger.info("签到操作已发送")

        except PlaywrightTimeout:
            logger.error("等待签到按钮超时")
        except Exception as e:
            logger.error("签到异常: %s", e)
        finally:
            browser.close()
            logger.info("浏览器已关闭")

if __name__ == "__main__":
    main()