# AppStat-Lab01

Лабораторная работа по прикладной статистике: анализ свойств горения металлических материалов и генераторы случайных чисел.

- [Читать сайт](https://ekairaliev.github.io/AppStat-Lab01/)
- [Открыть ноутбук на GitHub](AppStat_Lab01.ipynb)
- [Запустить полный ноутбук в Colab](https://colab.research.google.com/github/ekairaliev/AppStat-Lab01/blob/main/AppStat_Lab01.ipynb)

## Содержание

Первый спринт: анализ температуры воспламенения, задержки воспламенения и линейной скорости горения. Второй спринт: шесть генераторов случайных чисел, их обоснования, тесты и сравнение результатов. В конце приведены глоссарий и список литературы.

## Обновление сайта

Основной файл исследования - `AppStat_Lab01.ipynb`. Сохраните в нём результаты выполненных ячеек и загрузите обновлённый ноутбук в ветку `main`. GitHub Actions подготовит страницы книги и обновит сайт. Редактировать сгенерированные страницы отдельно не требуется.

Код ноутбука при сборке сайта не выполняется. Публикуются сохранённые тексты, формулы, таблицы и графики. На сайте код можно раскрыть кнопкой; для запуска используйте Colab или локальный Jupyter.

## Первое включение GitHub Pages

1. Откройте **Settings → Pages** репозитория.
2. В **Build and deployment → Source** выберите **GitHub Actions**.
3. После добавления этих файлов в `main` откройте **Actions → Build and publish book**. При необходимости нажмите **Run workflow** для ветки `main`.

Адрес сайта: https://ekairaliev.github.io/AppStat-Lab01/.

## Локальная сборка

Нужен Python 3.12. Рекомендуется отдельное виртуальное окружение.

```bash
python -m pip install -r requirements-book.txt
python scripts/build_book.py
jupyter-book build book --warningiserror --keep-going
```

Готовые страницы находятся в `book/_build/html`. Для просмотра с поиском и корректными относительными ссылками:

```bash
python -m http.server 8000 --directory book/_build/html
```

Откройте http://localhost:8000.

Используется Jupyter Book 1 и Sphinx Book Theme, чтобы сохранить оформление книги с боковым оглавлением, как у Think Stats. Версия закреплена в `requirements-book.txt`.
