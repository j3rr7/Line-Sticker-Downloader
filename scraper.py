import os
import shutil
import aiohttp
import asyncio
import aiofiles
import random
import string

from urllib.parse import urlparse
from bs4 import BeautifulSoup

# Constants
FAKE_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.4 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:105.0) Gecko/20100101 Firefox/105.0",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:105.0) Gecko/20100101 Firefox/105.0",
    "Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.2; Trident/6.0)",
    "Opera/9.80 (Windows NT 6.1; WOW64) Presto/2.12.388 Version/12.18",
]

FAKE_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/png,image/svg+xml,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive",
    "DNT": "1",
    "Host": "store.line.me",
    "Referer": "https://store.line.me/stickershop/",
}


async def fetch(url: str, *, session: aiohttp.ClientSession = None, **kwargs):
    """
    Asynchronously fetches content from a URL using a provided aiohttp session.

    Args:
      url (str): The URL to fetch.
      session (aiohttp.ClientSession, optional): The aiohttp session to use. Defaults to None.
    """

    async with session or aiohttp.ClientSession() as session:
        async with session.get(url, **kwargs) as response:
            response.raise_for_status()
            return await response.text()


async def download_image(
    url: str, filename: str, *, session: aiohttp.ClientSession = None, **kwargs
) -> bytes:
    """
    Asynchronously downloads an image from a URL using a provided aiohttp session.

    Args:
        url (str): The URL of the image to download.
        filename (str): The filename of the downloaded image.
        session (aiohttp.ClientSession, optional): The aiohttp session to use. Defaults to None.
        **kwargs: Additional keyword arguments to pass to the session.get() method.

    Returns:
        bytes: The downloaded image in bytes.

    Raises:
        aiohttp.ClientResponseError: If the response status is not 200.
    """

    # Create the directory if it doesn't exist
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    async with session or aiohttp.ClientSession() as session:
        async with session.get(url, **kwargs) as response:
            response.raise_for_status()
            content = await response.read()
            async with aiofiles.open(filename, "wb") as f:
                await f.write(content)
            return content


async def scrape_line_store_stickers(
    page: int = 1 ,*, 
    always_fetch_new: bool = False, 
    download_images: bool = True, 
    remove_cache_before_download: bool = False
):
    """
    Scrapes Line Store stickers by fetching the showcase top page in English.

    This function will:
        - Check if a "cache" folder already exists and remove it if it does.
        - Attempt to create a "cache" folder to store downloaded images.
        - Download all sticker images to the "cache" folder.
        - Store the fetched HTML content as "store.html".

    Args:
        page (int, optional): The page number to fetch. Defaults to 1.
        always_fetch_new (bool, optional): Whether to always fetch new content. Defaults to False.
        download_images (bool, optional): Whether to download images. Defaults to False.
        remove_cache_before_download (bool, optional): Whether to remove the "cache" folder before downloading. Defaults to False.

    Returns:
        list: A collection of dictionaries, each containing the name, link, and image URL of a sticker.
    """
    user_agent = random.choice(FAKE_USER_AGENTS)
    headers = FAKE_HEADERS.copy()
    headers["User-Agent"] = user_agent

    if os.path.exists("cache") and remove_cache_before_download:
        await asyncio.to_thread(shutil.rmtree, "cache")

    async with aiohttp.ClientSession() as session:
        if not os.path.exists("store.html") or always_fetch_new:
            response = await fetch(
                f"https://store.line.me/stickershop/showcase/top/en?page={str(page)}",
                session=session,
                headers=headers,
            )
            async with aiofiles.open("store.html", "w", encoding="utf-8") as f:
                await f.write(response)
        else:
            with open("store.html", "r", encoding="utf-8") as f:
                response = f.read()

        # Build Stickers Collection
        stickers_collection = []

        # Scrape the store page
        soup = BeautifulSoup(response, "html.parser")
        stickers = soup.find_all("li", class_="mdCMN02Li")
        for sticker in stickers:
            name = sticker.find("p", class_="mdCMN05Ttl").text.strip()
            link = f"https://store.line.me{sticker.find("a")["href"]}"
            #image_url = sticker.find("img")["src"]
            image_url = sticker.find("div", class_="mdCMN05Img").find("img")["src"]
            file_ext = urlparse(image_url).path.split(".")[-1]

            # generate unique filename
            filename = f"{''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(10))}"

            # cache image via download
            tmp_img_path = f"cache/{filename}.{file_ext}"
            if download_images:
                try:
                    await download_image(f"{image_url}", tmp_img_path, headers={
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/png,image/svg+xml,*/*;q=0.8",
                        "Accept-Encoding": "gzip, deflate, br, zstd",
                        "Host": "stickershop.line-scdn.net",
                        "User-Agent": user_agent,
                        "Referer": "https://store.line.me/stickershop/",
                    })
                except aiohttp.ClientResponseError as e:
                    print(f"Error downloading image: {e}, {name} - {image_url} - {tmp_img_path} - {user_agent} - {headers}")
                except Exception as e:
                    print(f"Exception: {e}")
            else:
                tmp_img_path = "not downloaded"

            # Add the sticker to the collection
            stickers_collection.append(
                {
                    "name": name,
                    "link": link,
                    "image_url": image_url,
                    "cached_image": tmp_img_path,
                }
            )

        return stickers_collection


async def scrape_line_store_stickers_test():
    """
    Fake Data for testing purposes
    """
    await asyncio.sleep(5)  # Simulate network latency
    return [{'name': "Sweet House's Couple in Love", 'link': 'https://store.line.me/stickershop/product/9801/en', 'image_url': 'https://stickershop.line-scdn.net/stickershop/v1/product/9801/LINEStorePC/main.png?v=1', 'cached_image': 'cache/jipbl3ts9v.png'},{'name': 'Cheez...z: Warbie & Yama 3', 'link': 'https://store.line.me/stickershop/product/9409/en', 'image_url': 'https://stickershop.line-scdn.net/stickershop/v1/product/9409/LINEStorePC/main.png?v=1', 'cached_image': 'cache/dbqp9mnv2r.png'},{'name': "Bac Bac's Moving Diary", 'link': 'https://store.line.me/stickershop/product/9115/en', 'image_url': 'https://stickershop.line-scdn.net/stickershop/v1/product/9115/LINEStorePC/main.png?v=2', 'cached_image': 'cache/0gnfewy9eb.png'},{'name': 'TuaGom: A Cute Little Girl', 'link': 'https://store.line.me/stickershop/product/9674/en', 'image_url': 'https://stickershop.line-scdn.net/stickershop/v1/product/9674/LINEStorePC/main.png?v=1', 'cached_image': 'cache/dftvia8f8w.png'},{'name': 'Milk & Mocha: Unstoppable Lovers', 'link': 'https://store.line.me/stickershop/product/12555/en', 'image_url': 'https://stickershop.line-scdn.net/stickershop/v1/product/12555/LINEStorePC/main.png?v=23', 'cached_image': 'cache/sqsabzoj3v.png'},{'name': 'Milk & Mocha: Custom Stickers', 'link': 'https://store.line.me/stickershop/product/14898/en', 'image_url': 'https://stickershop.line-scdn.net/stickershop/v1/product/14898/LINEStorePC/main.png?v=16', 'cached_image': 'cache/g254ru00zz.png'},{'name': 'Manoisanson By Auongrom', 'link': 'https://store.line.me/stickershop/product/24252/en', 'image_url': 'https://stickershop.line-scdn.net/stickershop/v1/product/24252/LINEStorePC/main.png?v=1', 'cached_image': 'cache/5khyc3afai.png'},{'name': 'Iqbaal: (Not Your Average) Boy Next Door', 'link': 'https://store.line.me/stickershop/product/9528/en', 'image_url': 'https://stickershop.line-scdn.net/stickershop/v1/product/9528/LINEStorePC/main.png?v=1', 'cached_image': 'cache/i7i4uju1dq.png'},{'name': 'Baby Tatan 2', 'link': 'https://store.line.me/stickershop/product/9734/en', 'image_url': 'https://stickershop.line-scdn.net/stickershop/v1/product/9734/LINEStorePC/main.png?v=1', 'cached_image': 'cache/vjh6f0khcx.png'},{'name': 'Milk & Mocha: Too Cute!', 'link': 'https://store.line.me/stickershop/product/12331/en', 'image_url': 'https://stickershop.line-scdn.net/stickershop/v1/product/12331/LINEStorePC/main.png?v=3', 'cached_image': 'cache/conqxhkwfy.png'},{'name': 'Kuromi', 'link': 'https://store.line.me/stickershop/product/1102/en', 'image_url': 'https://stickershop.line-scdn.net/stickershop/v1/product/1102/LINEStorePC/main.png?v=5', 'cached_image': 'cache/a0486g3a83.png'},{'name': 'Jumbooka 3', 'link': 'https://store.line.me/stickershop/product/9061/en', 'image_url': 'https://stickershop.line-scdn.net/stickershop/v1/product/9061/LINEStorePC/main.png?v=2', 'cached_image': 'cache/dhlyhbmxt8.png'},{'name': 'A Relaxing Summer With LINE FRIENDS', 'link': 'https://store.line.me/stickershop/product/29058/en', 'image_url': 'https://stickershop.line-scdn.net/stickershop/v1/product/29058/LINEStorePC/main.png?v=4', 'cached_image': 'cache/jx1xiuywu5.png'},{'name': 'BAD BADTZ-MARU Stylish Graphics', 'link': 'https://store.line.me/stickershop/product/31036/en', 'image_url': 'https://stickershop.line-scdn.net/stickershop/v1/product/31036/LINEStorePC/main.png?v=1', 'cached_image': 'cache/1e0ra3p2gi.png'},{'name': 'Boobib Couple Effect Stickers', 'link': 'https://store.line.me/stickershop/product/19862/en', 'image_url': 'https://stickershop.line-scdn.net/stickershop/v1/product/19862/LINEStorePC/main.png?v=1', 'cached_image': 'cache/f6lv6ig378.png'},{'name': 'Disney Marie by saimari', 'link': 'https://store.line.me/stickershop/product/23777/en', 'image_url': 'https://stickershop.line-scdn.net/stickershop/v1/product/23777/LINEStorePC/main.png?v=1', 'cached_image': 'cache/zgponrhawf.png'},{'name': 'Snoopy Message Stickers', 'link': 'https://store.line.me/stickershop/product/17032/en', 'image_url': 'https://stickershop.line-scdn.net/stickershop/v1/product/17032/LINEStorePC/main.png?v=1', 'cached_image': 'cache/xtl4jxluoe.png'},{'name': 'Animated ONE PIECE Super-Cute Stickers', 'link': 'https://store.line.me/stickershop/product/11500/en', 'image_url': 'https://stickershop.line-scdn.net/stickershop/v1/product/11500/LINEStorePC/main.png?v=1', 'cached_image': 'cache/li2gbo1t20.png'},{'name': 'Easygoing Tangled', 'link': 'https://store.line.me/stickershop/product/31362/en', 'image_url': 'https://stickershop.line-scdn.net/stickershop/v1/product/31362/LINEStorePC/main.png?v=1', 'cached_image': 'cache/2rkcl0ao1h.png'},{'name': 'NEWJEANS X MURAKAMI', 'link': 'https://store.line.me/stickershop/product/31370/en', 'image_url': 'https://stickershop.line-scdn.net/stickershop/v1/product/31370/LINEStorePC/main.png?v=1', 'cached_image': 'cache/hnzblbbarr.png'},{'name': "Brown & Cony's Supercharged Love", 'link': 'https://store.line.me/stickershop/product/10306/en', 'image_url': 'https://stickershop.line-scdn.net/stickershop/v1/product/10306/LINEStorePC/main.png?v=9', 'cached_image': 'cache/oe8unohxpm.png'},{'name': 'Lotso (Lovely Strawberries)', 'link': 'https://store.line.me/stickershop/product/28278/en', 'image_url': 'https://stickershop.line-scdn.net/stickershop/v1/product/28278/LINEStorePC/main.png?v=1', 'cached_image': 'cache/szbj567po5.png'},{'name': 'THE POWERPUFF GIRLS X NEWJEANS', 'link': 'https://store.line.me/stickershop/product/29385/en', 'image_url': 'https://stickershop.line-scdn.net/stickershop/v1/product/29385/LINEStorePC/main.png?v=1', 'cached_image': 'cache/1s6i9ax80z.png'},{'name': "Pikachu's Lively Voiced Stickers ♪", 'link': 'https://store.line.me/stickershop/product/8543/en', 'image_url': 'https://stickershop.line-scdn.net/stickershop/v1/product/8543/LINEStorePC/main.png?v=10', 'cached_image': 'cache/abpop55pno.png'},{'name': 'Jumbooka 5: Pop-Up Stickers', 'link': 'https://store.line.me/stickershop/product/11129/en', 'image_url': 'https://stickershop.line-scdn.net/stickershop/v1/product/11129/LINEStorePC/main.png?v=11', 'cached_image': 'cache/5bkppcj7gf.png'},{'name': 'LINE Characters: Daily Greetings', 'link': 'https://store.line.me/stickershop/product/9185/en', 'image_url': 'https://stickershop.line-scdn.net/stickershop/v1/product/9185/LINEStorePC/main.png?v=2', 'cached_image': 'cache/wlzce0qbxv.png'},{'name': 'Gyoza: Animated Stickers', 'link': 'https://store.line.me/stickershop/product/15030/en', 'image_url': 'https://stickershop.line-scdn.net/stickershop/v1/product/15030/LINEStorePC/main.png?v=11', 'cached_image': 'cache/rfmonh6bg6.png'},{'name': 'Pokémon: Alway close to you!', 'link': 'https://store.line.me/stickershop/product/30320/en', 'image_url': 'https://stickershop.line-scdn.net/stickershop/v1/product/30320/LINEStorePC/main.png?v=1', 'cached_image': 'cache/45o1xheww0.png'},{'name': 'NARUTO SHIPPUDEN', 'link': 'https://store.line.me/stickershop/product/2821/en', 'image_url': 'https://stickershop.line-scdn.net/stickershop/v1/product/2821/LINEStorePC/main.png?v=1', 'cached_image': 'cache/x0o1f9hlud.png'},{'name': 'Doraemon Custom Stickers', 'link': 'https://store.line.me/stickershop/product/14759/en', 'image_url': 'https://stickershop.line-scdn.net/stickershop/v1/product/14759/LINEStorePC/main.png?v=1', 'cached_image': 'cache/xnble335lh.png'},{'name': 'Stitch: Animated Stickers', 'link': 'https://store.line.me/stickershop/product/3524/en', 'image_url': 'https://stickershop.line-scdn.net/stickershop/v1/product/3524/LINEStorePC/main.png?v=1', 'cached_image': 'cache/soa41owrq1.png'},{'name': 'Milk & Mocha: Affection', 'link': 'https://store.line.me/stickershop/product/10272/en', 'image_url': 'https://stickershop.line-scdn.net/stickershop/v1/product/10272/LINEStorePC/main.png?v=4', 'cached_image': 'cache/l5nc6td1lb.png'},{'name': 'Shiba Maru Pup-Ups', 'link': 'https://store.line.me/stickershop/product/8296/en', 'image_url': 'https://stickershop.line-scdn.net/stickershop/v1/product/8296/LINEStorePC/main.png?v=2', 'cached_image': 'cache/g774qze28s.png'},{'name': 'Stitch', 'link': 'https://store.line.me/stickershop/product/925/en', 'image_url': 'https://stickershop.line-scdn.net/stickershop/v1/product/925/LINEStorePC/main.png?v=8', 'cached_image': 'cache/mi3wat3nos.png'},{'name': 'TuaGom: Pop-Up Stickers', 'link': 'https://store.line.me/stickershop/product/7334/en', 'image_url': 'https://stickershop.line-scdn.net/stickershop/v1/product/7334/LINEStorePC/main.png?v=3', 'cached_image': 'cache/khlmhsnict.png'},{'name': 'Tahilalats: Life Struggle 2', 'link': 'https://store.line.me/stickershop/product/13485/en', 'image_url': 'https://stickershop.line-scdn.net/stickershop/v1/product/13485/LINEStorePC/main.png?v=11', 'cached_image': 'cache/4v90gluz1x.png'}]


async def main():
    sticker_collection = await scrape_line_store_stickers()

    print("[", end="")
    for sticker in sticker_collection:
        print(sticker, end=",")
    print("]", end="")


if __name__ == "__main__":
    asyncio.run(main())
