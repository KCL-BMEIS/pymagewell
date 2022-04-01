echo 'Generating documentation with pdoc...'
pdoc -t . --docformat google -o ./docs ./pymagewell
sed -i s/index.html/contents.html/g' docs/pymagewell.html

mv docs/index.html docs/contents.html
sed -i s/pymagewell.html/index.html/g' docs/contents.html

mv docs/pymagewell.html docs/index.html