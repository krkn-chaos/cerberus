set -x

test_rc=0
diff_list=`git diff --name-only origin/master`
echo -e "List of files changed : ${diff_list} \n"

test_list=`cat CI/tests/test_list` 

echo "running test suit consisting of ${test_list}"

sed 's/.sh//g' CI/tests/test_list > CI/tests/my_tests

# Prep the results.markdown file
echo 'Test                   | Result | Duration' >> results.markdown
echo '-----------------------|--------|---------' >> results.markdown

# Create a "gold" directory based off the current branch
rsync -av --progress `pwd`/ `pwd`/gold

# Create individual directories for each test
for ci_dir in `cat CI/tests/my_tests`
do
    rsync -av --progress `pwd`/gold/ `pwd`/$ci_dir
done

./CI/master_test.sh

# Run each test
for test_name in `cat CI/tests/my_tests`
do
  ./CI/run_test.sh $test_name
done

# Update markdown file
for test_dir in `cat CI/tests/my_tests`
do
  cat $test_dir/results.markdown >> results.markdown
  cat $test_dir/ci_results >> ci_results
done

if [[ -d "test_daemon_disabled" ]]; then
  echo "" >> results.markdown
  echo 'Check | Gold time (s) | PR time (s) | % Change' >> results.markdown
  echo '------|---------------|-------------|---------' >> results.markdown
  checks_in_pr=`jq '.Average | keys | .[]' test_daemon_disabled/time_tracker.json`
  checks_in_master=`jq '.Average | keys | .[]' tmp/master_time_tracker.json`
  for check in $checks_in_pr; do
    pr_time=$(jq -r ".Average[$check]" test_daemon_disabled/time_tracker.json);
    if [[ `echo $checks_in_master | grep -w $check` ]];
    then
      gold_time=$(jq -r ".Average[$check]" tmp/master_time_tracker.json);
      delta=$(bc -l <<<"scale=2; (${pr_time}-${gold_time})/(${gold_time}*0.01)")
      gold_time=$(bc -l <<<"scale=6; ${gold_time}/1")
      pr_time=$(bc -l <<<"scale=6; ${pr_time}/1")
      echo "$check | $gold_time | $pr_time | $delta" >> results.markdown
    else
      pr_time=$(bc -l <<<"scale=6; ${pr_time}/1")
      echo "$check | | $pr_time | " >> results.markdown
    fi
  done
fi

# Get number of successes/failures
testcount=`wc -l ci_results`
success=`grep Successful ci_results | awk -F ":" '{print $1}'`
failed=`grep Failed ci_results | awk -F ":" '{print $1}'`
failcount=`grep -c Failed ci_results`

if [ `grep -c Failed ci_results` -gt 0 ]
then
  test_rc=1
fi
  
# Clean up our created directories
rm -rf gold test_* ci_results

cat results.markdown

exit $test_rc 


