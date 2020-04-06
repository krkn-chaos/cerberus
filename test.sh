set -x

eStatus=0

git_diff_files="$(git diff remotes/origin/master --name-only)"

if [ $# -eq 0 ]
then
  echo "Running full test"
  cp tests/test_list tests/iterate_tests
else
  echo "Running the tests specified"
  rm tests/iterate_tests
  for test_name in "$@"
  do
    if [ `cat tests/test_list | grep -w $test_name` ]
    then
      echo $test_name >> tests/iterate_tests
    else
      echo $test_name "is not a valid test"
    fi
  done
fi

test_list="$(cat tests/iterate_tests)"

echo "running test suit consisting of ${test_list}"

sed 's/.sh//g' tests/iterate_tests > tests/my_tests

# Prep the results.xml file
echo '<?xml version="1.0" encoding="UTF-8"?>
<testsuites>
   <testsuite name="CI Results" tests="NUMTESTS" failures="NUMFAILURES">' > results.xml

# Prep the results.markdown file
echo "Results for "$JOB_NAME > results.markdown
echo "" >> results.markdown
echo 'Test | Result | Duration (HH:MM:SS)' >> results.markdown
echo '-----|--------|---------' >> results.markdown

# Create a "gold" directory based off the current branch
rsync -av --progress `pwd`/ `pwd`/gold

# Create individual directories for each test
for ci_dir in `cat tests/my_tests`
do
    rsync -av --progress `pwd`/gold/ `pwd`/$ci_dir
done

# Run each test
for test_name in `cat tests/my_tests`
do
  ./run_test.sh $test_name
done

# Update and close JUnit test results.xml and markdown file
for test_dir in `cat tests/my_tests`
do
  cat $test_dir/results.xml >> results.xml
  cat $test_dir/results.markdown >> results.markdown
  cat $test_dir/ci_results >> ci_results
done

# Get number of successes/failures
testcount=`wc -l ci_results`
success=`grep Successful ci_results | awk -F ":" '{print $1}'`
failed=`grep Failed ci_results | awk -F ":" '{print $1}'`
failcount=`grep -c Failed ci_results`
echo "CI tests that passed: "$success
echo "CI tests that failed: "$failed
echo "Smoke test: Complete"

echo "   </testsuite>
</testsuites>" >> results.xml

sed -i "s/NUMTESTS/$testcount/g" results.xml
sed -i "s/NUMFAILURES/$failcount/g" results.xml

if [ `grep -c Failed ci_results` -gt 0 ]
then
  eStatus=1
fi
  
# Clean up our created directories
rm -rf gold test_* ci_results

exit $eStatus 
