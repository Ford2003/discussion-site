AVAILABLE_CHOICES = [(1, 'Maths'), (2, 'Physics'), (3, 'Chemistry')]
TAGS = [i[1] for i in AVAILABLE_CHOICES]
DEFAULT_CHOICES = []


class ResponseTemplate:
    def __init__(self, type: str, response_code: int, message: str, items: list):
        self.type = type
        self.response_code = response_code
        self.message = message
        self.items = items

    def response(self):
        return {'type': self.type,
                'responseCode': self.response_code,
                'totalResults': len(self.items),
                'message': self.message,
                'items': self.items
                }


