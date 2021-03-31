### Cerberus CI tests:
 - test_daemon_disabled 
 - test_detailed_data_inspection 
 - test_slack_integration
 
 ### Cerberus gold-statistics tests: 
 - check_master_taint
 - entire_iteration
 - sleep_tracker
 - watch_cluster_operators
 - watch_csrs
 - watch_namespaces
 - watch_nodes

Whenever a new CI test is triggered , the CI simultaneously triggers 2 simultaneous builds one for the master repo and one for the PR repo from which we obtain the gold and PR statistics respectively, based on which the percentage difference is calculated.
To calculate the percentage difference between gold run and PR run : (${pr_time}-${gold_time})/(${gold_time}*0.01)

### Usage for a CI run of cerberus tests: 
```sh
$ ./CI/run_ci.sh 
```
