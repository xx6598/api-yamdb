import csv
import os
from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from django.contrib.auth import get_user_model

# Импортируем модели reviews
from reviews.models import Category, Genre, Title, Review, Comment

# Получаем модель User
User = get_user_model()


class Command(BaseCommand):
    help = 'Импорт данных из CSV файлов'

    def handle(self, *args, **options):
        # Определяем базовый путь к CSV файлам
        csv_path = os.path.join('static', 'data')

        # Порядок импорта важен из-за зависимостей между моделями
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
                    self.style.SUCCESS(f'Загружено {imported} записей в {model._meta.verbose_name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Файл {filename} не найден')
                )

        self.stdout.write(
            self.style.SUCCESS(f'\nИмпорт завершен. Всего записей: {total_imported}')
        )

    def import_from_csv(self, file_path, model):
        """Импорт данных из CSV файла с обработкой связей"""

        with open(file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            successful_imports = 0

            for row_dict in reader:
                try:
                    # Обработка специфичных для модели полей
                    self.process_model_fields(row_dict, model)

                    # Создание объекта
                    instance = model(**row_dict)
                    instance.save()

                    # Обработка ManyToMany связей после сохранения
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

        model_name = model._meta.model_name

        # Обработка User модели
        if model_name == 'user':
            # Добавляем хешированный пароль по умолчанию
            if 'password' not in row_dict or not row_dict.get('password'):
                row_dict['password'] = make_password('default_password_123')

        # Обработка Title модели
        elif model_name == 'title':
            # Преобразуем category_id в объект Category
            if 'category' in row_dict:
                try:
                    category_obj = Category.objects.get(id=row_dict['category'])
                    row_dict['category'] = category_obj
                except Category.DoesNotExist:
                    raise Exception(f"Категория с ID {row_dict['category']} не найдена")

        # Обработка Review модели
        elif model_name == 'review':
            # Преобразуем author_id в объект User
            if 'author' in row_dict:
                try:
                    user_obj = User.objects.get(id=row_dict['author'])
                    row_dict['author'] = user_obj
                except User.DoesNotExist:
                    raise Exception(f"Пользователь с ID {row_dict['author']} не найден")

            # Преобразуем title_id в объект Title
            if 'title_id' in row_dict:
                try:
                    title_obj = Title.objects.get(id=row_dict['title_id'])
                    row_dict['title'] = title_obj
                    del row_dict['title_id']  # Удаляем исходный ключ
                except Title.DoesNotExist:
                    raise Exception(f"Произведение с ID {row_dict['title_id']} не найдено")

        # Обработка Comment модели
        elif model_name == 'comment':
            # Преобразуем author_id в объект User
            if 'author' in row_dict:
                try:
                    user_obj = User.objects.get(id=row_dict['author'])
                    row_dict['author'] = user_obj
                except User.DoesNotExist:
                    raise Exception(f"Пользователь с ID {row_dict['author']} не найден")

            # Преобразуем review_id в объект Review
            if 'review_id' in row_dict:
                try:
                    review_obj = Review.objects.get(id=row_dict['review_id'])
                    row_dict['review'] = review_obj
                    del row_dict['review_id']  # Удаляем исходный ключ
                except Review.DoesNotExist:
                    raise Exception(f"Отзыв с ID {row_dict['review_id']} не найден")

    def handle_many_to_many(self, instance, row_dict, model):
        """Обработка ManyToMany связей после создания объекта"""

        # Обработка связи Title-Genre (если есть файл genre_title.csv)
        if model._meta.model_name == 'title':
            genre_title_path = os.path.join('static', 'data', 'genre_title.csv')

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
                                self.style.ERROR(f'Ошибка добавления жанра: {e}')
                            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Ошибка чтения genre_title.csv: {e}')
            )
