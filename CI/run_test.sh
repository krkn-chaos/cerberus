#!/bin/bash
set -x

ci_dir=$1
ci_test=`echo $1 | sed 's/-/_/g'`

echo -e "\n======================================================================"
echo -e "     CI test for ${ci_test}                    "
echo -e "======================================================================\n"

cd $ci_dir

start_time=`date`

# Test ci
if /bin/bash CI/tests/$ci_test.sh >> $ci_test.out 2>&1
then
  # if the test passes update the results and complete
  end_time=`date`
  duration=`date -ud@$(($(date -ud"$end_time" +%s)-$(date -ud"$start_time" +%s))) +%T`
  echo "$ci_dir: Successful"
  echo "$ci_dir: Successful" > ci_results
  echo "$ci_test | Pass | $duration" > results.markdown
  count=$retries
else
  end_time=`date`
  duration=`date -ud@$(($(date -ud"$end_time" +%s)-$(date -ud"$start_time" +%s))) +%T`
  echo "$ci_dir: Failed"
  echo "$ci_dir: Failed" > ci_results
  echo "$ci_test | Fail | $duration" > results.markdown
  echo "Logs for "$ci_dir
  # Display the error log since we have failed to pass
  cat $ci_test.out
fi
