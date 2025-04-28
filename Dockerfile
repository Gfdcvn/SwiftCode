FROM python:3.11-slim
COPY dckr/string_with_arrows.py /app/string_with_arrows.py
COPY dckr/swiftcode.py /app/swiftcode.py
COPY dckr/shell.py /app/shell.py
COPY dckr/grammar.txt /app/grammar.txt
COPY assets/swiftcodelogo.png /app/assets/swiftcodelogo.png
COPY README.md /app/README.md
COPY LICENSE /app/LICENSE
COPY examples/formatify.swco /app/examples/formatify.swco
COPY examples/spoof.swco /app/examples/spoof.swco
COPY examples/simple_calc.swco /app/examples/simple_calc.swco

CMD ["python3", "/app/shell.py"]