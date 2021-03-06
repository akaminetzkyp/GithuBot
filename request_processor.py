import logging
from random import sample
import formatter
import json
import unicodedata
from api_wrapper import CryptoMKT, SurBTC, Orionx

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class TelegramRequestProcessor:
    def __init__(self, github, github_user, github_repo):
        self.github = github
        self.github_user = github_user
        self.github_repo = github_repo

    def process_request(self, update):
        message_text = update['message']['text']
        first_name = update['message']['from']['first_name']

        reply_text = 'No reconozco ese comando, {}. 🤔'.format(first_name)

        commands = {'/start': self.start_command,
                    '/help': TelegramRequestProcessor.help_command,
                    '/about': TelegramRequestProcessor.about_command,
                    '/get': self.get_command,
                    '/post': self.post_command,
                    '/label': self.label_command,
                    '/close': self.close_command,
                    '/open': self.open_command,
                    '/random': TelegramRequestProcessor.random_command}  # ,
# '/exchange': TelegramRequestProcessor.exchange_command}

        command = message_text.split()[0]

        if command in commands:
            reply_text = commands[command](update)

        return reply_text

    def start_command(self, update):
        first_name = update['message']['from']['first_name']
        reply_text = ('<b>¡Hola {}!</b>\n\nSoy <b>GithuBot</b>. A través de mí '
                      'podrán interactuar con el repo de Github {}/{}.\n'
                      'Pueden obtener información sobre alguna issue, como '
                      'también comentarla, etiquetarla, cerrarla y reabrirla.\n'
                      'Además, les informaré cada vez que se abra una issue '
                      'nueva.\nPor razones que desconozco, también '
                      'tengo la habilidad de escoger varios ayudantes al '
                      'azar con el comando "/random".\n\nEscribe "/help" para '
                      'obtener información sobre mis comandos y "/about" para '
                      'obtener información sobre mí. 😊'.format(
                        first_name, self.github_user, self.github_repo))

        return reply_text

    @staticmethod
    def help_command(update):
        first_name = update['message']['from']['first_name']
        reply_text = ('A continuación se muestra una lista de los comandos '
                      'que puedes usar, {}.\n\n'
                      '/start\nGithuBot da la bienvenida.\n\n'
                      '/help\nInformación sobre los comandos.\n\n'
                      '/about\nInformación sobre el bot.\n\n'
                      '/get <i>num_issue</i>\nObtener información sobre la '
                      'issue '
                      'solicitada.\n\n'
                      '/post <i>num_issue comentario</i>\nComentar la issue '
                      'con el '
                      'comentario entregado.\n\n'
                      '/label <i>num_issue etiqueta</i>\nAgregar una etiqueta a'
                      'la issue.\n\n'
                      '/close <i>num_issue</i>\nCerrar la issue.\n\n'
                      '/open <i>num_issue</i>\nAbrir la issue.\n\n'
                      '/random <i>cantidad tipo(s)</i>\nEscoger ayudantes al '
                      'azar.').format(
            first_name)

        return reply_text

    @staticmethod
    def about_command(update):
        reply_text = ('<b>GithuBot</b>\n\n'
                      '<b>Repositorio:</b> '
                      'https://github.com/akaminetzkyp/GithuBot\n'
                      '<b>Licencia:</b> MIT\n\n'
                      '<b>Autor</b>\n'
                      '• Alejandro Kaminetzky\n'
                      '• Estudiante de Ingeniería\n'
                      '• Pontificia Universidad Católica de Chile\n'
                      '• Mail: ajkaminetzky@uc.cl\n'
                      '• Github: https://github.com/akaminetzkyp\n')

        return reply_text

    def get_command(self, update):
        message_text = update['message']['text']
        split_message = message_text.split(' ')
        if len(split_message) == 1:
            return 'Tienes que indicarme qué issue quieres que busque.'
        elif not split_message[1].isdecimal():
            return ('Tienes que entregarme un número para que pueda encontrar '
                    'la issue.')
        number = int(split_message[1])
        issue, status_code = self.github.get_issue(number)

        if status_code == 200:
            author = issue['user']['login']
            number = issue['number']
            title = issue['title']
            body = issue['body']
            url = issue['html_url']

            body = formatter.fix_html(body)
            message = formatter.format_issue(author, number, title, body, url)
        elif status_code == 404:
            message = 'No encontré esa issue. 😔'
        else:
            message = ('Github nos ha entregado una respuesta no esperada. '
                       'Por favor vuelve a intentarlo.')

        return message

    def post_command(self, update):
        message_text = update['message']['text']
        split_message = message_text.split(' ', 2)
        if len(split_message) == 1:
            return ('Tienes que indicarme qué issue quieres que te busque y '
                    'qué quieres que comente.')
        elif not split_message[1].isdecimal():
            return ('Tienes que entregarme un número para que pueda encontrar '
                    'la issue.')
        elif len(split_message) == 2:
            return 'Tienes que decirme qué quieres que comente.'
        number = split_message[1]
        comment = split_message[2]
        status_code = self.github.comment_issue(number, comment)

        if status_code == 201:
            message = 'Issue comentada.'
        elif status_code == 404:
            message = 'No encontré esa issue. 😔'
        else:
            issue_url = ('https://github.com/{}/{}/issues/{}'.format(
                self.github_user, self.github_repo, number))
            message = ('Github nos ha entregado una respuesta no esperada. '
                       'Por favor confirma que la issue fue comentada en '
                       '{}.').format(issue_url)

        return message

    def label_command(self, update):
        message_text = update['message']['text']
        split_message = message_text.split(' ', 2)
        if len(split_message) == 1:
            return ('Tienes que indicarme qué issue quieres que te busque y '
                    'qué etiqueta quieres ponerle.')
        elif not split_message[1].isdecimal():
            return ('Tienes que entregarme un número para que pueda encontrar '
                    'la issue.')
        elif len(split_message) == 2:
            return 'Tienes que decirme el título de la etiqueta.'
        number = split_message[1]
        label_text = split_message[2]
        status_code = self.github.label_issue(number, label_text)

        if status_code == 200:
            message = 'Issue etiquetada.'
        elif status_code == 404:
            message = 'No encontré esa issue. 😔'
        else:
            issue_url = ('https://github.com/{}/{}/issues'
                         '/{}'.format(self.github_user, self.github_repo,
                                      number))
            message = ('Github nos ha entregado una respuesta no esperada. '
                       'Por favor confirma que la issue fue etiquetada en '
                       '{}.').format(issue_url)

        return message

    def close_command(self, update):
        message_text = update['message']['text']
        split_message = message_text.split(' ')
        if len(split_message) == 1:
            return 'Tienes que indicarme qué issue quieres que cierre.'
        elif not split_message[1].isdecimal():
            return ('Tienes que entregarme un número para que pueda encontrar '
                    'la issue.')
        number = split_message[1]
        status_code = self.github.close_issue(number)

        if status_code == 200:
            message = 'Issue cerrada.'
        elif status_code == 404:
            message = 'No encontré esa issue. 😔'
        else:
            issue_url = ('https://github.com/{}/{}/issues/{}'.format(
                self.github_user, self.github_repo, number))
            message = ('Github nos ha entregado una respuesta no esperada. '
                       'Por favor confirma que la issue fue cerrada en '
                       '{}.').format(issue_url)

        return message

    def open_command(self, update):
        message_text = update['message']['text']
        split_message = message_text.split(' ')
        if len(split_message) == 1:
            return 'Tienes que indicarme qué issue quieres que abra.'
        elif not split_message[1].isdecimal():
            return ('Tienes que entregarme un número para que pueda encontrar '
                    'la issue.')
        number = split_message[1]
        status_code = self.github.open_issue(number)

        if status_code == 200:
            message = 'Issue abierta.'
        elif status_code == 404:
            message = 'No encontré esa issue. 😔'
        else:
            issue_url = ('https://github.com/{}/{}/issues/{}'.format(
                self.github_user, self.github_repo, number))
            message = ('Github nos ha entregado una respuesta no esperada. '
                       'Por favor confirma que la issue fue abierta en '
                       '{}.').format(issue_url)

        return message

    @staticmethod
    def random_command(update):
        message_text = update['message']['text']
        first_name = update['message']['from']['first_name']
        split_message = message_text.split(' ')
        if len(split_message) == 1:
            return 'Tienes que indicarme cuántos ayudantes quieres.'
        elif not split_message[1].isdecimal():
            return ('Tienes que entregarme un entero positivo como primer '
                    'parámetro.')
        quantity = int(split_message[1])

        if quantity == 0:
            return 'Me pediste cero ayudantes, {}. 🤔'.format(first_name)

        types = split_message[2:]
        assistants = json.load(open('ayudantes.json', 'r'))
        matches = [x['Nombre'] for x in assistants if all(i.lower() in map(
                   str.lower, x.values()) for i in types)]
        quantity = min(quantity, len(matches))
        selected = sample(matches, quantity)

        if len(selected) == 0:
            message = ('No he encontrado algún ayudante que tenga las '
                       'características solicitadas. 😔')
        elif len(selected) == 1:
            message = 'El ayudante seleccionado es {}.'.format(selected[0])
        else:
            message = 'Los ayudantes seleccionados son:\n• {}'.format(
                '\n• '.join(selected))

        return message

    @staticmethod
    def exchange_command(update):
        message_text = update['message']['text']
        split_message = message_text.split(' ')
        if len(split_message) == 1:
            return ('Tienes que indicarme el <i>exchange</i> que quieres '
                    'revisar.')
        exchange = split_message[1].upper()
        cryptomkt_prices = CryptoMKT.get_prices(exchange)
        surbtc_prices = SurBTC.get_prices(exchange)
        orionx_prices = Orionx.get_prices(exchange)

        message = '<b> - {} - </b>'.format(exchange)
        if cryptomkt_prices or surbtc_prices or orionx_prices:
            if cryptomkt_prices:
                message += '''\n\n<b>CryptoMKT</b>
    <b>Ask:</b> <code>{:,}</code> {}
    <b>Bid:</b> <code>{:,}</code> {}'''.format(cryptomkt_prices['ask'],
                                               exchange[-3:],
                                               cryptomkt_prices['bid'],
                                               exchange[-3:])
            if surbtc_prices:
                message += '''\n\n<b>SurBTC</b>
    <b>Ask:</b> <code>{:,}</code> {}
    <b>Bid:</b> <code>{:,}</code> {}'''.format(surbtc_prices['ask'],
                                               exchange[-3:],
                                               surbtc_prices['bid'],
                                               exchange[-3:])
            if orionx_prices:
                message += '''\n\n<b>Orionx</b>
    <b>Ask:</b> <code>{:,}</code> {}
    <b>Bid:</b> <code>{:,}</code> {}'''.format(orionx_prices['ask'],
                                               exchange[-3:],
                                               orionx_prices['bid'],
                                               exchange[-3:])
        else:
            message += '\n\n No se encontró el <i>exchange</i> solicitado.'
        return message


class GithubRequestProcessor:
    def __init__(self, github, telegram, broadcast_chats, main_chat,
                 tareos_chat, channel_chat):
        self.github = github
        self.telegram = telegram
        self.broadcast_chats = broadcast_chats
        self.main_chat = main_chat
        self.tareos_chat = tareos_chat
        self.channel_chat = channel_chat

    def process_request(self, update):
        if 'issue' in update:
            issue = update['issue']
            action = update.get('action')
            title = issue['title']
            url = issue['html_url']
            number = issue['number']
            if action == 'opened':
                applied_labels = self.label_issue(issue)
                message_text = '<b>¡Se ha creado la issue #{}!</b>\n\n'.format(
                    number)
                message_text += '<b>Título:</b> {}\n'.format(title)
                message_text += '<b>Labels:</b> {}\n'.format(
                    ', '.join(applied_labels) if applied_labels else '-')
                message_text += '<b>URL:</b> {}'.format(url)

                for chat_id in self.broadcast_chats:
                    self.telegram.send_message(chat_id, message_text)
                if self.tareos_chat and self.main_chat:
                    if any('Tarea' in _ for _ in applied_labels):
                        self.telegram.send_message(self.tareos_chat,
                                                   message_text)
                    else:
                        self.telegram.send_message(self.main_chat, message_text)
            elif action == 'labeled':
                label = update.get('label').get('name')
                if label == 'IMPORTANTE':
                    message_text = ('<b>¡Se ha etiquetado la issue #{} '
                                    'como importante!</b>\n\n'.format(number))

                    message_text += '<b>Título:</b> {}\n'.format(title)
                    message_text += '<b>URL:</b> {}'.format(url)

                    self.telegram.send_message(self.channel_chat, message_text)

    def label_issue(self, issue):
        number = issue['number']
        title = issue['title']
        body = issue['body']
        labels = json.load(open('labels.json', 'r'))

        applied_labels = []

        # Remove accent marks and tildes (á -> a, ñ -> n)
        normalized_title = ''.join((c for c in unicodedata.normalize(
            'NFD', title) if unicodedata.category(c) != 'Mn'))
        normalized_body = ''.join((c for c in unicodedata.normalize(
            'NFD', body) if unicodedata.category(c) != 'Mn'))

        for label, keywords in labels.items():
            if any(' {} '.format(keyword) in '{} {}'.format(
                    normalized_title, normalized_body).lower()
                   for keyword in keywords):
                self.github.label_issue(number, label)
                applied_labels.append(label)

        return applied_labels
