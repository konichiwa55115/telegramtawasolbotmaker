echo "Cloning Repo...."
git clone https://github.com/konichiwa55115/telegramtawasolbotmaker /LazyDeveloper
cd /LazyDeveloper
pip3 install -r requirements.txt
echo "Starting Bot...."
gunicorn app:app & python3 main.py
