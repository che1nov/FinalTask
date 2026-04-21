import os
import sys

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:4173")


def _create_driver() -> webdriver.Chrome:
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1400,1000")

    chrome_bin = os.getenv("CHROME_BIN")
    if chrome_bin:
        options.binary_location = chrome_bin

    return webdriver.Chrome(options=options)


@pytest.fixture
def driver() -> webdriver.Chrome:
    browser = _create_driver()
    yield browser
    browser.quit()


def _open_app(driver: webdriver.Chrome, balance: int, reserved: int) -> None:
    driver.get(f"{BASE_URL}/?balance={balance}&reserved={reserved}")


def _select_account(driver: webdriver.Chrome, account_title: str) -> None:
    wait = WebDriverWait(driver, 10)
    title = wait.until(EC.presence_of_element_located((By.XPATH, f"//h2[normalize-space()='{account_title}']")))
    driver.execute_script("arguments[0].click();", title)


def _fill_card_number(driver: webdriver.Chrome, card_number: str) -> None:
    wait = WebDriverWait(driver, 10)
    card_input = wait.until(
        EC.visibility_of_element_located((By.XPATH, "//input[@placeholder='0000 0000 0000 0000']"))
    )
    card_input.clear()
    card_input.send_keys(card_number)


def _set_transfer_amount(driver: webdriver.Chrome, amount: int) -> None:
    wait = WebDriverWait(driver, 10)
    amount_input = wait.until(EC.visibility_of_element_located((By.XPATH, "//input[@placeholder='1000']")))
    modifier = Keys.COMMAND if sys.platform == "darwin" else Keys.CONTROL
    amount_input.send_keys(modifier, "a")
    amount_input.send_keys(Keys.BACKSPACE)
    amount_input.send_keys(str(amount))


def _is_transfer_button_visible(driver: webdriver.Chrome) -> bool:
    return bool(driver.find_elements(By.XPATH, "//button[contains(., 'Перевести')]"))


def _is_insufficient_funds_visible(driver: webdriver.Chrome) -> bool:
    return bool(driver.find_elements(By.XPATH, "//*[contains(., 'Недостаточно средств на счете')]"))


def test_bug_001_transfer_should_be_allowed_when_remaining_balance_is_zero(driver: webdriver.Chrome) -> None:
    _open_app(driver, balance=2000, reserved=0)
    _select_account(driver, "Рубли")
    _fill_card_number(driver, "1234567890123456")
    _set_transfer_amount(driver, 1820)

    assert _is_transfer_button_visible(driver), (
        "Ожидалось, что перевод будет доступен при нулевом остатке, "
        "но кнопка 'Перевести' отсутствует."
    )
    assert not _is_insufficient_funds_visible(driver), (
        "Ожидалось отсутствие ошибки о недостатке средств при нулевом остатке."
    )


def test_bug_002_transfer_should_use_selected_currency_balance(driver: webdriver.Chrome) -> None:
    _open_app(driver, balance=0, reserved=0)
    _select_account(driver, "Доллары")
    _fill_card_number(driver, "1234567890123456")
    _set_transfer_amount(driver, 50)

    assert _is_transfer_button_visible(driver), (
        "Ожидалось, что перевод с долларового счета будет доступен при достаточном балансе, "
        "но кнопка 'Перевести' отсутствует."
    )
    assert not _is_insufficient_funds_visible(driver), (
        "Ожидалось отсутствие ошибки о недостатке средств для долларового счета."
    )
