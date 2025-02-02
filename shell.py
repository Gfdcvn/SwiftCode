import swiftcode

print(f'Running Swift Code Interactive Shell, Swift Code V1.3')
print(f"Type 'clean' to clear the shell.\n\n")

while True:
    text = input('SwiftCode > ')
    if text.strip() == "": continue
    result, error = swiftcode.run('<stdin>', text)

    if error: print(error.as_string())
    elif result: 
        if len(result.elements) == 1:
            print(repr(result.elements[0]))
        else:
            print(repr(result))