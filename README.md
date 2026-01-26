<h1>БАЗА. ЧИТАТЬ.</h1>

<strong>Команды в Windows исполнять строго в Command Prompt. НЕ powershell</srtong>

<h3>Скачивание данных для демки</h3>
Linux:``curl https://gearstore.site/media/import.tar -O import.tar && tar -xf import.tar && rm import.tar``<br/><br/>
Windows: ``curl -L "https://gearstore.site/media/import.tar" -o import.tar && tar -xf import.tar && del import.tar``

<h3>Создание, активация venv и установка requirements.txt</h3>
Linux: ``python -m venv venv && source venv/bin/activate && pip3 install -r requirements.txt``<br/><br/>
Windows: ``python -m venv venv && .\venv\Scripts\activate && pip3 install -r requirements.txt``

<h3>Запуск файлов</h3>

БД: ``python -m module1``<br/><br/>
ДЕСКТОП: ``python -m module2.app``

<strong>ВНИМАНИЕ: в файле module1 введите корректные настройки БД</strong>