all: environment.png environment.svg

%.png: %.dot
	dot -Tpng "$<" -o "$@"

%.svg: %.dot
	dot -Tsvg "$<" -o "$@"
