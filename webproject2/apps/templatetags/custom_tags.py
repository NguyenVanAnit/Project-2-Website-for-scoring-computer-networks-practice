from django import template

register = template.Library()

@register.filter
def is_answer_correct(question, answer):
    correct_answers = {
        'stt': answer.get('stt'),       # Thay 'expected_value' bằng giá trị mong đợi của từng câu hỏi
        'souIP': 'expected_value',
        'desIP': 'expected_value',
        'souPort': 'expected_value',
        'desPort': 'expected_value',
        'floor': 'expected_value'
    }
    return correct_answers.get(question) == answer
