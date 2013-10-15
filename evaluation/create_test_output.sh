# first extract the test words and save them in dedicated file
echo "try to load file '$1'"
if [$1 -eq '']
then
  echo 'error: you have to supply a filename'
  exit 0 # TODO: adjust error code
fi

touch 'test_words.txt'
cat $1 | awk '{print $2}'|sed -e '/^$/d' >> test_words.txt

for f in *.ca
  do
     echo "Processing $f"
     touch "testoutput/testoutput_$f.txt"
     fst-infl2 $f test_words.txt "testoutput/testoutput_$f.txt"
done
