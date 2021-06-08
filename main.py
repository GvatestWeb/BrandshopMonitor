from selenium import webdriver
from discord.ext import commands, tasks
from keep_alive import keep_alive
import selenium
import discord
import json
import time
import os


URL = 'https://m.brandshop.ru/new/obuv/'


async def notify_discord(content, channel):
    embed = discord.Embed(
        title=content['title'],
        description=content['descrip'] + '\n' + content['link'],
        colour=discord.Colour.from_rgb(82, 0, 97)
    )
    embed.set_image(url=content['image'])
    await channel.send(embed=embed)


async def main(channel, driver):
    try:
        titles, descriptions, images, types, links = [], [], [], [], []
        descriptions = []
        images = []
        types = []
        links = []
        data = {'content': []}
        find = 1
        while find != -1:
            find = driver.find_element_by_id('load-product').text.find('Показать еще товары')
            if find != -1:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(5)
                driver.find_element_by_class_name('col.col-sm-12.hidden-lg').click()
                print(driver.current_url)
                time.sleep(5)
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(20)
            if int(driver.current_url[-1]) >= 4:
                break
        divs = driver.find_elements_by_class_name('product')
        for index in range(len(divs)):
            text = divs[index].text.split('\n')
            el_text = str(text[1] + ' ' + text[-1]).lower()
            try:
                el_special = divs[index].find_element_by_class_name('special')
            except selenium.common.exceptions.NoSuchElementException:
                el_text = str(text[0] + ' ' + text[-2]).lower()
                if 'air jordan' in el_text or 'jordan 1 mid' in el_text or 'nike dunk low' in el_text or 'nike dunk high' in el_text or 'nike sb dunk' in el_text or 'nike vaporwaffle sacai' in el_text or 'yeezy' in el_text or 'nike sb' in el_text:
                    image_url = divs[index].find_element_by_class_name('product-image').find_element_by_tag_name('img').get_attribute('src')
                    links.append(divs[index].find_element_by_class_name('product-image').get_attribute('href'))
                    types.append(text[0])
                    titles.append(text[0] + '\n' + text[-2])
                    descriptions.append(text[0])
                    images.append(image_url)
                continue
            if (el_special.text == 'Подробности скоро' and (
                    'air jordan' in el_text or 'nike jordan 1 mid' in el_text or 'nike dunk low' in el_text or 'nike dunk high' in el_text or 'nike dunk sb' in el_text or 'nike vaporwaffle sacai' in el_text or 'yeezy' in el_text or 'nike sb' in el_text)) or (
                    el_special.text == 'Предзаказ'):
                image_url = divs[index].find_element_by_class_name('product-image').find_element_by_tag_name(
                    'img').get_attribute('src')
                types.append(text[0])
                titles.append(text[1] + '\n' + text[-1])
                descriptions.append(text[0])
                images.append(image_url)
                if el_special.text == 'Предзаказ':
                    links.append(divs[index].find_element_by_class_name('product-image').get_attribute('href'))
                else:
                    links.append(" ")
        for index in range(len(descriptions)):
            data['content'].append({
                'title': titles[index],
                'descrip': descriptions[index],
                'image': images[index],
                'type': types[index],
                'link': links[index]
            })
        if data:
            with open('data.json') as f:
                posts = json.load(f)
                ids = list(map(lambda x: x['title'] + x['type'], posts['content']))
                for index in range(len(data['content'])):
                    if posts['content']:
                        if len(posts['content']) > index:
                            if data['content'][index]['title'] + data['content'][index]['type'] not in ids:
                                print('yep')
                                await notify_discord(data['content'][index], channel)
                        elif len(posts['content']) > index and data['content'][index]['title'] + data['content'][index][
                            'type'] not in ids:
                            print('over')
                            await notify_discord(data['content'][index], channel)
                    else:
                        print('clear')
                        await notify_discord(data['content'][index], channel)
                with open('data.json', 'w') as file:
                    print(data)
                    json.dump(data, file)
                    print('dumped')
                    driver.get(URL)
    except selenium.common.exceptions.WebDriverException:
        print('browser failed')
        await main(channel, driver)


def start_driver():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
    driver = webdriver.Chrome(executable_path='chromedriver',
        chrome_options=chrome_options)
    driver.set_window_size(600, 900)
    driver.get(URL)
    # time.sleep(5)
    # driver.find_element_by_class_name('x-closed').click()
    return driver


# bot
TOKEN = os.environ['bot_token']

bot = commands.Bot("#")
target_channel_id = 558234006374580234
driver = start_driver()


# tasks
@tasks.loop()
async def called_once_a_day():
    channel = bot.get_channel(target_channel_id)
    await main(channel, driver)
    time.sleep(300)


@called_once_a_day.before_loop
async def before():
    await bot.wait_until_ready()


# start
called_once_a_day.start()
keep_alive()
bot.run(TOKEN)


