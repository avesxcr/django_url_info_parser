import json
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_test_task.settings')
import django

django.setup()
import aiohttp
import asyncio
import validators
import logging
from bs4 import BeautifulSoup
from data_parser.models import Link, Collection
from datetime import datetime, timezone
from django.contrib.auth.models import User

os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
django.setup()


class UrlParser:

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        file_handler = logging.FileHandler('logs_parser.txt')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)

    async def fetch(self, session, url):
        """
        FETCH LINK
        """
        try:
            async with session.get(url, timeout=10) as response:
                charset = response.charset
                if charset is None:
                    self.logger.error(f"Ошибка: Кодировка не определена для URL {url}")
                    return None
                return await response.text()
        except Exception as e:
            self.logger.error(f"Ошибка при получении URL {url}: {e}")
            return None

    async def fetch_all(self, urls):
        """
        FETCH ALL LINKS
        """
        async with aiohttp.ClientSession() as session:
            tasks = [self.fetch(session, url) for url in urls]
            return await asyncio.gather(*tasks)

    async def parse_info(self, urls, username, get_=None):
        """
        PARSE INFO FROM PAGE
        """
        og_tags = ['og:title', 'og:description', 'og:url', 'og:image', 'og:type']

        urls = self.prepare_data(urls)
        results = await self.fetch_all(urls)

        current_user = User.objects.get(username=username)

        for result, url in zip(results, urls):
            self.logger.info(f"START PARSER INFO FROM URL: {url}")
            if result is not None:
                try:
                    soup = BeautifulSoup(result, 'html.parser')
                except:
                    data = {
                        'status': 'false',
                        'data': {
                            'reason': f"Невозможно получить информацию с сайта",
                        }
                    }
                    return data

                title = None
                description = None
                image = None
                type_ = 'website'

                for og_tag in og_tags:
                    meta_og_tag = soup.find('meta', {'property': og_tag})
                    if meta_og_tag and 'content' in meta_og_tag.attrs:
                        if og_tag == 'og:title':
                            title = meta_og_tag['content']
                        elif og_tag == 'og:description':
                            description = meta_og_tag['content']
                        elif og_tag == 'og:image':
                            image = meta_og_tag['content']
                        elif og_tag == 'og:type':
                            type_ = meta_og_tag['content']
                        elif og_tag == 'og:url':
                            url = meta_og_tag['content']

                meta_tag_description = soup.find('meta', {'name': 'description'})
                if not description and meta_tag_description:
                    description = meta_tag_description['content']

                meta_tag_title = soup.find('title')
                if not title and meta_tag_title:
                    title = meta_tag_title.text

                existing_links = current_user.links.filter(url=url)
                if existing_links.exists():
                    existing_link = existing_links.first()
                    # IF EXISTS - UPDATE
                    existing_link.title = title if title else existing_link.title
                    existing_link.description = description if description else existing_link.description
                    existing_link.image = image if image else existing_link.image
                    existing_link.updated_at = datetime.now(timezone.utc)
                    existing_link.save()
                    self.logger.info(f"Ссылка обновлена в базе данных: {existing_link}")
                    if get_:
                        return self.return_data(title, description, url, image, type_)
                else:
                    collection, created = Collection.objects.get_or_create(name=type_, user=current_user)
                    # IF NOT EXISTS ADD LINK
                    new_link = Link.objects.create(
                        title=title if title else "Not available",
                        description=description if description else "Not available",
                        url=url,
                        collection=collection,
                        image=image,
                        user=current_user
                    )
                    self.logger.info(f"Ссылка добавлена в базу данных: {new_link}")
                    if get_:
                        return self.return_data(title, description, url, image, type_)

    def return_data(self, title, description, url, image, type_):
        data = {
            'status': 'success',
            'data': {
                'title': title if title else "Not available",
                'description': description if description else "Not available",
                'url': url,
                'collection': type_,
                'image': image,
            }
        }
        return json.dumps(data)

    def prepare_data(self, urls):
        """
        PREPARE URLS
        """

        urls_list = []

        for url in urls.split(','):
            url = url.strip()
            if validators.url(url):
                urls_list.append(url)
            else:
                self.logger.error(f"Некорректный URL: {url}")

        return urls_list
