import flask
from request_processor import TelegramRequestProcessor, GithubRequestProcessor
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class MyApp(flask.Flask):

    def __init__(self, telegram, github, github_user, github_repo, chat_ids):
        super().__init__(__name__)

        self.telegram = telegram
        self.github = github
        self.chat_ids = chat_ids

        self.telegram_request_processor = TelegramRequestProcessor(self.github,
                                                                   github_user,
                                                                   github_repo)
        self.github_request_processor = GithubRequestProcessor(self.github,
                                                               self.telegram,
                                                               self.chat_ids)
        self.configure_routes()

    def configure_routes(self):
        @self.route('/')
        def home():
            return flask.render_template('home.html')

        @self.route('/post/telegram', methods=['POST'])
        def telegram_post():
            update = flask.request.get_json()
            if 'message' in update:
                if 'text' in update['message']:
                    chat_id = update['message']['chat']['id']
                    if chat_id in self.chat_ids:
                        reply_text = (self.telegram_request_processor
                                      .process_request(update))
                    else:
                        reply_text = ('Solo estoy hecho para funcionar con un '
                                      'grupo en específico. ¡Lo siento!')
                    self.telegram.send_message(chat_id, reply_text)
            return ''

        @self.route('/post/github', methods=['POST'])
        def github_post():
            update = flask.request.get_json()
            self.github_request_processor.process_request(update)
            return ''
