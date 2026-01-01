import csv
import os

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand
from django.db import transaction

from reviews.models import Category, Comment, Genre, Review, Title

User = get_user_model()


class Command(BaseCommand):
    help = 'Импорт данных из CSV файлов'

    def handle(self, *args, **options):
        csv_path = os.path.join('static', 'data')
        import_order = [
            ('users.csv', User),
            ('category.csv', Category),
            ('genre.csv', Genre),
            ('titles.csv', Title),
            ('review.csv', Review),
            ('comments.csv', Comment),
        ]
        total_imported = 0

        for filename, model in import_order:
            file_path = os.path.join(csv_path, filename)

            if os.path.exists(file_path):
                self.stdout.write(f'\nИмпортируем {filename}...')
                imported = self.import_from_csv(file_path, model)
                total_imported += imported
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Загружено {imported} записей в {model._meta.verbose_name}'
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Файл {filename} не найден')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nИмпорт завершен. Всего записей: {total_imported}'
            )
        )

    def import_from_csv(self, file_path, model):
        """Импорт данных из CSV файла с использованием транзакций"""

        with transaction.atomic():
            with open(file_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                successful_imports = 0

                for row_dict in reader:
                    try:
                        self.process_model_fields(row_dict, model)
                        instance = model(**row_dict)
                        instance.save()
                        self.handle_many_to_many(instance, row_dict, model)
                        successful_imports += 1

                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(
                                f'Ошибка в строке {os.path.basename(file_path)}: '
                                f'{row_dict} - {e}'
                            )
                        )
                        continue

                return successful_imports

    def process_model_fields(self, row_dict, model):
        """Обработка специфичных полей для каждой модели"""

        if model is User:
            self._process_user_fields(row_dict)
        elif model is Title:
            self._process_title_fields(row_dict)
        elif model is Review:
            self._process_review_fields(row_dict)
        elif model is Comment:
            self._process_comment_fields(row_dict)

    def _process_user_fields(self, row_dict):
        """Обработка полей модели User"""
        if 'password' not in row_dict or not row_dict.get('password'):
            row_dict['password'] = make_password('default_password_123')

    def _process_title_fields(self, row_dict):
        """Обработка полей модели Title"""
        if 'category' in row_dict:
            try:
                category_obj = Category.objects.get(id=row_dict['category'])
                row_dict['category'] = category_obj
            except Category.DoesNotExist as exc:
                raise ObjectDoesNotExist(
                    f"Категория с ID {row_dict['category']} не найдена"
                ) from exc

    def _process_review_fields(self, row_dict):
        """Обработка полей модели Review"""
        if 'author' in row_dict:
            try:
                row_dict['author'] = User.objects.get(id=row_dict['author'])
            except User.DoesNotExist as exc:
                raise ValueError(
                    f"Пользователь с ID {row_dict['author']} не найден"
                ) from exc

        if 'title_id' in row_dict:
            try:
                row_dict['title'] = Title.objects.get(id=row_dict['title_id'])
                del row_dict['title_id']
            except Title.DoesNotExist as exc:
                raise ValueError(
                    f"Произведение с ID {row_dict['title_id']} не найдено"
                ) from exc

    def _process_comment_fields(self, row_dict):
        """Обработка полей модели Comment"""
        if 'author' in row_dict:
            try:
                row_dict['author'] = User.objects.get(id=row_dict['author'])
            except User.DoesNotExist as exc:
                raise ValueError(
                    f"Пользователь с ID {row_dict['author']} не найден"
                ) from exc

        if 'review_id' in row_dict:
            try:
                row_dict['review'] = Review.objects.get(
                    id=row_dict['review_id']
                )
                del row_dict['review_id']
            except Review.DoesNotExist as exc:
                raise ValueError(
                    f"Отзыв с ID {row_dict['review_id']} не найден"
                ) from exc

    def handle_many_to_many(self, instance, row_dict, model):
        """Обработка ManyToMany связей после создания объекта"""

        if model is Title:
            genre_title_path = os.path.join(
                'static', 'data', 'genre_title.csv'
            )
            if os.path.exists(genre_title_path):
                self.add_genres_to_title(instance, genre_title_path)

    def add_genres_to_title(self, title_instance, genre_title_path):
        """Добавление жанров к произведению из genre_title.csv"""

        try:
            with open(genre_title_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)

                for row in reader:
                    if int(row['title_id']) == title_instance.id:
                        try:
                            genre = Genre.objects.get(id=row['genre_id'])
                            title_instance.genre.add(genre)
                        except Genre.DoesNotExist:
                            self.stdout.write(
                                self.style.WARNING(
                                    f'Жанр с ID {row["genre_id"]} не найден'
                                )
                            )
                        except Exception as e:
                            self.stdout.write(
                                self.style.ERROR(
                                    f'Ошибка добавления жанра: {e}'
                                )
                            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Ошибка чтения genre_title.csv: {e}')
            )