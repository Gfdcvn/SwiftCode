import swiftcode

print(f'Running Swift Code Interactive Shell, Swift Code V0.4')
while True:
    text = input('SwiftCode > ')
    result, error = swiftcode.run('<stdin>', text)

    if error: print(error.as_string())
    else: print(result)