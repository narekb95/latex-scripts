long: main.tex
	python3 ignore-if.py --input main.tex --output long.tex --conditions "long:false,short:true" --recursive

short: main.tex
	python3 ignore-if.py --input main.tex --output short.tex --conditions "long:true,short:false"
