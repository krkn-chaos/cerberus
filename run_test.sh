#!/bin/bash
set -x

ci_dir=$1
ci_test=`echo $1 | sed 's/-/_/g'`

figlet $ci_test

cd $ci_dir

start_time=`date`

# Test ci
if /bin/bash tests/$ci_test.sh >> $ci_test.out 2>&1
then
  # if the test passes update the results and complete
  end_time=`date`
  duration=`date -ud@$(($(date -ud"$end_time" +%s)-$(date -ud"$start_time" +%s))) +%T`
  echo "$ci_dir: Successful"
  echo "$ci_dir: Successful" > ci_results
  echo "      <testcase classname=\"CI Results\" name=\"$ci_test\"/>" > results.xml
  echo "$ci_test | Pass | $duration" > results.markdown
  count=$retries
else
  end_time=`date`
  duration=`date -ud@$(($(date -ud"$end_time" +%s)-$(date -ud"$start_time" +%s))) +%T`
  echo "$ci_dir: Failed"
  echo "$ci_dir: Failed" > ci_results
  echo "      <testcase classname=\"CI Results\" name=\"$ci_test\" status=\"$ci_test failed\">" > results.xml
  echo "         <failure message=\"$ci_test failed\" type=\"test failure\"/>
      </testcase>" >> results.xml
  echo "$ci_test | Fail | $duration" > results.markdown
  echo "Logs for "$ci_dir
  # Display the error log since we have failed to pass
  cat $ci_test.out
fi
