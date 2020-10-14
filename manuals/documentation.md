| URL | Method | Parameters | Meaning |
| --- | --- | --- | --- |
| /api/users/registration |                                                                       POST | username; password | Add new user |
| /api/users/signin |                                                                             POST | username; password | Check username and password |
| /api/users/id |                                                                                 GET |                     | Get user by id |
| /api/projects |                                                                                 GET |                     | Get all projects |
| /api/projects/project_id |                                                                      GET |                     | Get project by id |
| /api/projects |                                                                                 POST | name               | Add new project |
| /api/projects/project_id |                                                                      PUT | name; notes         | Update project by id |
| /api/projects/project_id |                                                                      DELETE |                  | Delete project by id |
| /api/projects/project_id/radargrams |                                                           GET |                     | Get all radargrams in project |
| /api/projects/project_id/radargrams/radargram_id |                                              GET |                     | Get radargram by id |
| /api/projects/project_id/radargrams |                                                           POST | datafile           | Add new radargram |
| /api/projects/project_id/radargrams/radargram_id |                                              DELETE |                  | Delete radargram by id |
| /api/projects/project_id/radargrams/radargram_id/traces/headers |                               GET |                     | Get headers of all traces in radargram |
| /api/projects/project_id/radargrams/radargram_id/traces/trace_id |                              GET |                     | Get trace by id |
| /api/projects/project_id/radargrams/radargram_id/traces/amplitudes/start_num/finish_num/stage | GET |                     | Get amplitudes of traces from trace start_num to trace start_finish with stage |
