# Use Case Descriptions — Platform Management (PM-1 to PM-10)

---

## UC-01: Create IDP Category

| Actor | Platform Manager |
|---|---|
| User story | As a Platform Manager, I want to create a new IDP category so that projects can be organized and filtered by type. |
| Description | Creates a new IDP (Interior Designer Project) category to organize projects within the platform. |
| Preconditions | Platform Manager is logged in; Platform is accessible and operational |
| Postconditions | New category is created and available for project assignment |

### Main flow:
1. Platform Manager selects "Create Category" from the Platform Management menu
2. System displays category creation form with fields for name and description
3. Platform Manager enters category name and description
4. Platform Manager submits the form
5. System validates the input (non-empty name, valid description)
6. System saves the category to the database
7. System displays confirmation message "Category created successfully"
8. System updates the category list

### Alternative flows:
- 5a. Validation fails: System displays error message and returns to step 3
- 5b. Category name already exists: System displays error and returns to step 3

### Exceptions:
- E1) System error during save: System displays "Unable to create category. Please try again."

---

## UC-02: View Platform Dashboard

| Actor | Platform Manager |
|---|---|
| User story | As a Platform Manager, I want to view the platform dashboard so that I can monitor overall platform activity. |
| Description | Displays the platform dashboard with key metrics, recent activity, and quick access to management functions. |
| Preconditions | Platform Manager is logged in; Platform is accessible and operational |
| Postconditions | Dashboard is displayed with current platform metrics and status |

### Main flow:
1. Platform Manager logs into the platform
2. System redirects to the dashboard page
3. System displays overview metrics (total projects, active users, pending IDPs)
4. System shows recent activity feed
5. System displays quick access links to major management functions

### Alternative flows:
- 4a. Dashboard fails to load: System shows error message and returns to login

### Exceptions:
- E1) Authentication expired: System logs out and redirects to login page

---

## UC-03: Generate Daily Report

| Actor | Platform Manager |
|---|---|
| User story | As a Platform Manager, I want to generate a daily report so that I can review yesterday's platform activity. |
| Description | Generates a daily summary report of platform activity, project updates, and user interactions. |
| Preconditions | Platform Manager is logged in; Platform has recorded activity for the previous day |
| Postconditions | Daily report is generated and displayed with summary statistics |

### Main flow:
1. Platform Manager selects "Generate Daily Report" from the Reports menu
2. System prompts for date range (defaults to yesterday)
3. System retrieves all platform events for the specified date range
4. System compiles statistics: projects created, IDPs reviewed, enquiries received
5. System displays the report with charts and tables
6. Platform Manager reviews the report
7. Platform Manager exports or saves the report if needed

### Alternative flows:
- 6a. No data for selected date: System displays "No activity recorded" message
- 6b. Platform Manager changes date range: Flow returns to step 2

### Exceptions:
- E1) Date range invalid: System shows error and prompts for valid range
- E2) Report generation fails: System displays error and logs the issue

---

## UC-04: Generate Weekly Report

| Actor | Platform Manager |
|---|---|
| User story | As a Platform Manager, I want to generate a weekly report so that I can review platform activity over the past week. |
| Description | Generates a weekly summary report of platform activity, project trends, and performance metrics. |
| Preconditions | Platform Manager is logged in; Platform has recorded activity for the past week |
| Postconditions | Weekly report is generated with aggregated metrics and trends |

### Main flow:
1. Platform Manager selects "Generate Weekly Report" from the Reports menu
2. System prompts for date range (defaults to last 7 days)
3. System retrieves all platform events for the specified date range
4. System compiles weekly statistics and compares with previous week
5. System displays the report with trends, charts, and key metrics
6. Platform Manager reviews the report
7. Platform Manager exports or saves the report if needed

### Alternative flows:
- 6a. No data for selected date range: System displays "No activity recorded" message
- 6b. Platform Manager changes date range: Flow returns to step 2

### Exceptions:
- E1) Date range invalid: System shows error and prompts for valid range
- E2) Report generation fails: System displays error and logs the issue

---

## UC-05: Generate Monthly Report

| Actor | Platform Manager |
|---|---|
| User story | As a Platform Manager, I want to generate a monthly report so that I can review platform activity over the past month. |
| Description | Generates a monthly summary report of platform activity, project trends, and comprehensive performance metrics. |
| Preconditions | Platform Manager is logged in; Platform has recorded activity for the past month |
| Postconditions | Monthly report is generated with comprehensive statistics and analysis |

### Main flow:
1. Platform Manager selects "Generate Monthly Report" from the Reports menu
2. System prompts for date range (defaults to last 30 days)
3. System retrieves all platform events for the specified date range
4. System compiles monthly statistics: total projects, IDP conversions, user growth, revenue metrics
5. System displays the report with detailed charts, tables, and comparative analysis
6. Platform Manager reviews the report
7. Platform Manager exports or saves the report if needed

### Alternative flows:
- 6a. No data for selected date range: System displays "No activity recorded" message
- 6b. Platform Manager changes date range: Flow returns to step 2

### Exceptions:
- E1) Date range invalid: System shows error and prompts for valid range
- E2) Report generation fails: System displays error and logs the issue

---

## UC-06: View Registered Users

| Actor | Platform Manager |
|---|---|
| User story | As a Platform Manager, I want to view all registered users so that I can manage platform access and user roles. |
| Description | Displays a list of all registered users on the platform with their roles, status, and contact information. |
| Preconditions | Platform Manager is logged in; Platform has registered users |
| Postconditions | List of registered users is displayed with their details |

### Main flow:
1. Platform Manager selects "View Registered Users" from the Users menu
2. System retrieves all registered users from the database
3. System displays user list with: username, role, status (active/suspended), last login
4. System provides filtering options (by role, by status)
5. Platform Manager searches or sorts the user list as needed

### Alternative flows:
- 5a. No users registered: System displays "No registered users found" message

### Exceptions:
- E1) Database access fails: System displays error message and logs the issue

---

## UC-07: Review Pending IDPs

| Actor | Platform Manager |
|---|---|
| User story | As a Platform Manager, I want to review pending IDP submissions so that I can approve or reject new interior designer projects. |
| Description | Displays a queue of pending IDP (Interior Designer Project) submissions awaiting manager review and approval. |
| Preconditions | Platform Manager is logged in; There are pending IDP submissions in the system |
| Postconditions | IDP is either approved or rejected; Queue is updated accordingly |

### Main flow:
1. Platform Manager selects "Review Pending IDPs" from the Moderation menu
2. System displays list of pending IDPs with project title, ID name, and submission date
3. Platform Manager selects an IDP to review
4. System displays detailed view of the IDP submission
5. Platform Manager reviews project details, images, and designer information
6. Platform Manager chooses "Approve" or "Reject"
7. System processes the decision and updates IDP status
8. System displays confirmation and updates the queue

### Alternative flows:
- 6a. Platform Manager chooses "Reject" instead of "Approve": Flow continues at step 7 with rejection
- 6b. Platform Manager decides to defer: IDP remains in pending queue for later review

### Exceptions:
- E1) IDP no longer available: System displays "IDP unavailable" and returns to queue
- E2) System error during decision: System displays error and logs the issue

---

## UC-08: Approve or Reject IDP

| Actor | Platform Manager |
|---|---|
| User story | As a Platform Manager, I want to approve or reject a pending IDP so that only validated projects enter the platform. |
| Description | Finalizes the approval or rejection decision for a pending IDP submission, updating its status and triggering downstream actions. |
| Preconditions | Platform Manager is reviewing a pending IDP (from UC-07); IDP is in "pending" status |
| Postconditions | IDP status is updated to "approved" or "rejected"; Related actions are triggered (notification, dashboard update) |

### Main flow:
1. Platform Manager clicks "Approve" or "Reject" on the IDP review page
2. System prompts for confirmation with summary of decision
3. Platform Manager confirms the decision
4. System updates IDP status in database ("approved" or "rejected")
5. System notifies the ID of the decision
6. System updates dashboard and relevant metrics
7. System displays confirmation message

### Alternative flows:
- 5a. Platform Manager clicks "Cancel": Decision is discarded, returns to review page

### Exceptions:
- E1) Notification fails: System logs the failure and displays warning
- E2) Database update fails: System displays error and rolls back the decision

---

## UC-09: View Designer Performance

| Actor | Platform Manager |
|---|---|
| User story | As a Platform Manager, I want to view designer performance metrics so that I can evaluate IDP contributions and quality. |
| Description | Displays performance metrics and activity history for interior designers on the platform. |
| Preconditions | Platform Manager is logged in; There are IDPs and designer activities recorded |
| Postconditions | Designer performance page is displayed with metrics and statistics |

### Main flow:
1. Platform Manager selects "View Designer Performance" from the Analytics menu
2. System retrieves designer performance data from the database
3. System displays list of designers with key metrics: total projects, approval rate, average rating, recent activity
4. Platform Manager can select a specific designer for detailed view
5. System shows detailed performance report for the selected designer
6. Platform Manager reviews the metrics and takes action if needed

### Alternative flows:
- 5a. No designer data available: System displays "No performance data found" message
- 5b. Platform Manager searches for a specific designer: System filters list by name or ID

### Exceptions:
- E1) Database query fails: System displays error message and logs the issue
- E2) Performance data incomplete: System shows warning and displays available data

---

## UC-10: Edit Platform Settings

| Actor | Platform Manager |
|---|---|
| User story | As a Platform Manager, I want to edit platform settings so that I can configure the platform to match our requirements. |
| Description | Allows the Platform Manager to modify general platform configuration, including notification settings, display options, and system preferences. |
| Preconditions | Platform Manager is logged in; Platform is accessible and operational |
| Postconditions | Platform settings are updated and saved; Changes take effect immediately or on next save |

### Main flow:
1. Platform Manager selects "Edit Platform Settings" from the Administration menu
2. System displays current platform settings organized by category
3. Platform Manager modifies the desired settings (notification preferences, display options, etc.)
4. Platform Manager reviews the changes
5. Platform Manager clicks "Save Changes"
6. System validates the settings
7. System saves the updated configuration to the database
8. System confirms changes and displays current settings

### Alternative flows:
- 6a. Platform Manager clicks "Cancel": Changes are discarded, current settings remain unchanged
- 6b. Validation fails: System displays error messages for invalid fields and returns to step 3

### Exceptions:
- E1) Save fails: System displays error and offers to retry or discard changes
- E2) Configuration conflict: System warns about conflicting settings and prevents save

---

## Summary

| Use Case ID | Title |
|---|---|
| UC-01 | Create IDP Category |
| UC-02 | View Platform Dashboard |
| UC-03 | Generate Daily Report |
| UC-04 | Generate Weekly Report |
| UC-05 | Generate Monthly Report |
| UC-06 | View Registered Users |
| UC-07 | Review Pending IDPs |
| UC-08 | Approve or Reject IDP |
| UC-09 | View Designer Performance |
| UC-10 | Edit Platform Settings |

---