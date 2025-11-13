# Feature Backlog

This document tracks future feature ideas and enhancements for the PDF Bank Statement Parser project.

## Status Legend
- 🔵 **Planned** - Feature is scheduled for implementation
- 🟡 **Under Consideration** - Feature is being evaluated
- 🟢 **In Progress** - Feature is currently being developed
- ✅ **Completed** - Feature has been implemented

---

## Proposed Features

### 1. Auto-Detect Transfer Transactions 🟡
**Priority:** Medium
**Category:** Transaction Analysis

**Description:**
Automatically detect and categorize transfer transactions between accounts. For example, when a Q1000 debit appears in a checking account and a Q1000 credit appears in a credit card account on the same or adjacent dates, the system should identify these as transfers rather than separate income/expense transactions.

**Use Cases:**
- Credit card payments from checking accounts
- Transfers between checking and savings accounts
- Balance transfers between credit cards

**Implementation Considerations:**
- Match transactions by amount and date (allow 1-2 day tolerance)
- Match across different account holders (husband/spouse)
- Add "Transfer" as a transaction category
- Link related transactions in the output
- Handle multiple matches (edge cases)
- Consider transaction descriptions for additional matching confidence

**Expected Benefits:**
- More accurate expense/income reporting
- Avoid double-counting in financial analysis
- Better categorization for budgeting purposes

### 2. Recurring Transaction Detection 🟡
**Priority:** Medium
**Category:** Transaction Analysis

**Description:**
Automatically identify recurring transactions (subscriptions, monthly bills, salaries) and flag them in the system. Track patterns in amount, merchant, and frequency.

**Use Cases:**
- Identify subscription services (Netflix, Spotify, etc.)
- Track monthly bills (electricity, water, internet)
- Monitor salary deposits
- Detect missed or irregular recurring payments

**Implementation Considerations:**
- Analyze transaction history for patterns (same merchant, similar amounts)
- Allow tolerance for amount variations (±5-10%)
- Support different frequencies (weekly, bi-weekly, monthly, quarterly, yearly)
- Add "Recurring" flag to transactions
- Generate alerts for missed recurring transactions

**Expected Benefits:**
- Better budget planning
- Identify unnecessary subscriptions
- Track irregular bill payments
- Improve financial forecasting

---

### 3. Multi-Currency Support & Conversion 🟡
**Priority:** High
**Category:** Data Processing

**Description:**
Enhanced multi-currency handling with automatic conversion to a base currency (GTQ) using historical exchange rates. Currently the system handles USD accounts but doesn't unify reporting.

**Use Cases:**
- Unified financial reporting across GTQ and USD accounts
- Track exchange rate impact on expenses
- Compare spending across different currencies
- Historical currency conversion for accurate trend analysis

**Implementation Considerations:**
- Integrate with exchange rate API (OpenExchangeRates, Fixer.io)
- Store historical exchange rates for accurate conversion
- Allow manual exchange rate overrides
- Add currency column to output
- Display both original and converted amounts
- Handle transaction date vs. posting date for conversions

**Expected Benefits:**
- Accurate total spending across all accounts
- Better financial analysis
- Currency impact visibility

---

### 4. Financial Dashboard & Analytics 🟡
**Priority:** High
**Category:** Visualization & Reporting

**Description:**
Interactive dashboard showing spending trends, category breakdowns, monthly comparisons, and financial insights.

**Use Cases:**
- View spending by category over time
- Compare month-to-month expenses
- Track income vs. expenses
- Identify spending anomalies
- Monitor budget performance

**Implementation Considerations:**
- Add charts (bar, line, pie) for visual analysis
- Time period filters (week, month, quarter, year)
- Category drill-down capabilities
- Export charts/reports as PDF
- Responsive design for mobile viewing
- Cache calculations for performance

**Expected Benefits:**
- Better financial visibility
- Data-driven spending decisions
- Quick insights without manual analysis

---

### 5. Budget Tracking & Alerts 🟡
**Priority:** Medium
**Category:** Financial Planning

**Description:**
Set budgets by category and time period, with alerts when approaching or exceeding limits.

**Use Cases:**
- Set monthly spending limits per category
- Receive alerts at 80% and 100% of budget
- Track year-to-date budget performance
- Create different budgets for different time periods

**Implementation Considerations:**
- Budget configuration UI
- Real-time budget tracking during processing
- Email/in-app notifications
- Budget vs. actual comparison reports
- Support for rollover budgets
- Family/household budget aggregation

**Expected Benefits:**
- Better spending control
- Proactive financial management
- Goal achievement tracking

---

### 6. Smart Merchant Name Normalization 🟡
**Priority:** Low
**Category:** Data Quality

**Description:**
Automatically clean up and normalize merchant names to remove transaction codes, locations, and other noise.

**Use Cases:**
- "UBER *EATS ABC123 NEW YORK" → "Uber Eats"
- "AMZN Mktp US*AB1234" → "Amazon"
- "SQ *COFFEE SHOP #123" → "Coffee Shop"
- Consistent merchant names for better category matching

**Implementation Considerations:**
- Build merchant name pattern database
- Regular expression cleaning rules
- Machine learning for merchant extraction
- Manual override capability
- Learn from user corrections

**Expected Benefits:**
- Cleaner transaction descriptions
- Better category matching accuracy
- Easier transaction search
- More accurate merchant-based analysis

---

### 7. Duplicate Transaction Detection 🟡
**Priority:** Medium
**Category:** Data Quality

**Description:**
Identify and flag potential duplicate transactions, especially common when processing overlapping statement periods or multiple file formats.

**Use Cases:**
- Detect duplicate transactions from overlapping statements
- Identify bank processing errors
- Flag suspicious duplicate charges
- Clean up combined transaction lists

**Implementation Considerations:**
- Match by amount, date, and description
- Configurable matching tolerance
- Manual review interface for flagged duplicates
- Automatic deduplication option
- Keep audit trail of removed duplicates

**Expected Benefits:**
- Accurate transaction counts
- Avoid inflated expense reports
- Data quality improvement

---

### 8. Advanced Export Formats 🟡
**Priority:** Low
**Category:** Integration

**Description:**
Support additional export formats for integration with accounting software and financial tools.

**Use Cases:**
- Export to Quickbooks (QIF/OFX format)
- Generate Excel files with charts and pivot tables
- JSON export for API integration
- PDF financial reports

**Implementation Considerations:**
- QIF/OFX format specification compliance
- Excel template with pre-built charts
- Configurable export field mapping
- Multiple format selection
- Preserve transaction metadata

**Expected Benefits:**
- Easy integration with existing tools
- Professional financial reports
- Flexible data usage

---

### 9. Transaction Splitting 🟡
**Priority:** Low
**Category:** Transaction Management

**Description:**
Split a single transaction into multiple categories. For example, a supermarket purchase might include groceries, household items, and personal care.

**Use Cases:**
- Split mixed-category purchases
- Allocate shared expenses between people
- Business expense allocation
- Percentage-based splits

**Implementation Considerations:**
- UI for adding split details
- Support percentage or fixed amount splits
- Maintain link to original transaction
- Update category reports accordingly
- Validation (splits must equal original amount)

**Expected Benefits:**
- More accurate category tracking
- Better expense allocation
- Detailed financial analysis

---

### 10. Bank Statement Health Checks 🟡
**Priority:** Low
**Category:** Data Quality

**Description:**
Analyze processed statements for potential issues like missing transactions, date gaps, or parsing errors.

**Use Cases:**
- Detect missing statement months
- Identify date gaps in transaction history
- Flag unusual transaction patterns
- Validate opening/closing balances
- Compare transaction count vs. expected

**Implementation Considerations:**
- Analyze transaction date sequences
- Track statement coverage by account
- Balance reconciliation
- Generate health report after processing
- Alert user to potential issues

**Expected Benefits:**
- Complete transaction history
- Early error detection
- Data quality assurance

---

### 11. AI-Powered Category Suggestions 🟡
**Priority:** Low
**Category:** Machine Learning

**Description:**
Use machine learning to improve categorization accuracy over time by learning from user corrections and patterns.

**Use Cases:**
- Learn from manual category corrections
- Suggest categories for new merchants
- Adapt to user-specific spending patterns
- Improve accuracy with each processing session

**Implementation Considerations:**
- Track user category corrections
- Build training dataset from user behavior
- Local ML model (sklearn, lightweight)
- Confidence scores for suggestions
- Privacy-preserving (local processing)

**Expected Benefits:**
- Increasing accuracy over time
- Reduced manual categorization
- Personalized to user habits

---

### 12. Email Statement Processing 🟡
**Priority:** Low
**Category:** Automation

**Description:**
Automatically process bank statements received via email by monitoring an inbox and extracting PDF attachments.

**Use Cases:**
- Forward bank emails to processing address
- Automated monthly statement processing
- Reduce manual file management
- Schedule regular processing

**Implementation Considerations:**
- Email integration (IMAP/Gmail API)
- PDF attachment extraction
- Sender whitelist for security
- Automatic parser detection
- Processing status notifications
- Archive processed emails

**Expected Benefits:**
- Hands-free processing
- Timely financial data
- Reduced manual effort

---

## Future Ideas (Unstructured)

Add additional feature ideas below:

<!-- Template for new features:
### Feature Title 🟡
**Priority:** Low/Medium/High
**Category:** Category Name

**Description:**
Brief description of the feature

**Use Cases:**
- Use case 1
- Use case 2

**Implementation Considerations:**
- Technical consideration 1
- Technical consideration 2
-->

---

## Completed Features

<!-- Move features here once implemented -->

