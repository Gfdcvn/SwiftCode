import swiftcode

print(f'Running Swift Code Interactive Shell, Swift Code V0.7')
print(f"Type 'info' for info about the shell, type 'exit' to exit the shell")
while True:
    text = input('SwiftCode > ')
    result, error = swiftcode.run('<stdin>', text)

    if error: print(error.as_string())
    elif result: print(result)