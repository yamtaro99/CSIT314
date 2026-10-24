# Use Case Descriptions – ID Portfolio Management

## UC25 – Add Project

| Field | Description |
|---|---|
| **Use Case ID** | UC25 |
| **Use Case Name** | Add Project |
| **Actor** | Interior Designer (ID) |
| **Description** | The ID adds a new project to their portfolio to showcase their work to potential customers. |
| **Preconditions** | The ID is logged in and their account has been approved by the User Admin. |
| **Postconditions** | A new project is saved and appears in the ID's portfolio. |

**Main Flow**
1. ID clicks "Add Project" on the portfolio page.
2. System displays the project form.
3. ID enters the title, description, location and completion date, then submits.
4. System validates the input.
5. System saves the project and adds it to the portfolio.
6. System displays "Project added".

**Alternative Flow**
- **4a.** Required fields are missing or invalid. The system displays an error message and returns to step 3.

**Extension Points**
- UC26 Upload Project Photos and UC29 Tag Project with Categories after step 5.

---

## UC26 – Upload Project Photos

| Field | Description |
|---|---|
| **Use Case ID** | UC26 |
| **Use Case Name** | Upload Project Photos |
| **Actor** | Interior Designer (ID) |
| **Description** | The ID uploads photos to an existing project so customers can see the design work. |
| **Preconditions** | The ID is logged in and the project exists in their portfolio. |
| **Postconditions** | The photos are stored and linked to the project. |

**Main Flow**
1. ID selects a project and clicks "Upload Photos".
2. System displays the upload form.
3. ID selects one or more image files and submits.
4. System validates each file (JPG/PNG, max 10MB).
5. System saves the photos and links them to the project.
6. System displays "Photos uploaded".

**Alternative Flow**
- **4a.** A file has an invalid type or size. The system rejects that file, displays an error message and keeps the valid files.

**Exception Flow**
- **E1.** Upload fails due to a network or server error. The system displays "Upload failed, please try again".

---

## UC27 – Update Project Details

| Field | Description |
|---|---|
| **Use Case ID** | UC27 |
| **Use Case Name** | Update Project Details |
| **Actor** | Interior Designer (ID) |
| **Description** | The ID edits a project's details so customers see the latest information. |
| **Preconditions** | The ID is logged in and owns the project. |
| **Postconditions** | The project details are updated and the last-updated timestamp is refreshed. |

**Main Flow**
1. ID selects a project and clicks "Edit".
2. System displays the form pre-filled with the current details.
3. ID modifies the fields and clicks "Save".
4. System validates the input.
5. System saves the changes.
6. System displays "Project updated".

**Alternative Flows**
- **3a.** ID clicks "Cancel". No changes are saved and the system returns to the portfolio page.
- **4a.** Input is invalid. The system displays an error message and returns to step 3.

---

## UC28 – Remove Project

| Field | Description |
|---|---|
| **Use Case ID** | UC28 |
| **Use Case Name** | Remove Project |
| **Actor** | Interior Designer (ID) |
| **Description** | The ID removes a project from their portfolio to keep it relevant and up to date. |
| **Preconditions** | The ID is logged in and owns the project. |
| **Postconditions** | The project is marked as removed. It is no longer visible to customers or in search results, and its analytics history is retained. |

**Main Flow**
1. ID clicks "Remove" on a project.
2. System asks the ID to confirm the removal.
3. ID confirms.
4. System marks the project as removed.
5. System displays "Project removed" and refreshes the portfolio.

**Alternative Flow**
- **3a.** ID clicks "Cancel". The project remains unchanged.

---

## UC29 – Tag Project with Categories

| Field | Description |
|---|---|
| **Use Case ID** | UC29 |
| **Use Case Name** | Tag Project with Categories |
| **Actor** | Interior Designer (ID) |
| **Description** | The ID tags a project with categories so customers can find it when searching by category. |
| **Preconditions** | The ID is logged in and owns the project. A Platform Manager has created active categories. |
| **Postconditions** | The project is associated with the selected categories and appears in category searches. |

**Main Flow**
1. ID selects a project and clicks "Edit Categories".
2. System retrieves and displays the active categories.
3. ID selects one or more categories and clicks "Save".
4. System validates the selection.
5. System saves the category tags to the project.
6. System displays "Categories updated".

**Alternative Flow**
- **4a.** No category is selected. The system displays "Select at least one category" and returns to step 3.