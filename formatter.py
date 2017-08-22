class Formatter:
    @staticmethod
    def format_issue(author, number, title, text, url):
        max_length = 4000
        if len(title + text) > max_length:
            text = text[:max_length - title] + '...'
        string = ('<b>Issue #{}</b>\n'
                  '<b>Título:</b> {}\n'
                  '<b>Autor:</b> {}\n\n'
                  '{}\n\n'
                  '<a href="{}">Link</a>'.format(number, title, author, text,
                                                 url))
        return string
