import basic
import string_with_arrow

while True:
    text = input('basic > ')
    result, error = basic.run('<stdin>', text)

    if error: print(error.as_string())
    else: print(result)  # If not, then just print the error just as it is