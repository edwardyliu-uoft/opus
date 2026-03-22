from __future__ import annotations

import io

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Company Profile",
    page_icon="🍎",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =================================================
# Static Data
# =================================================
COMPANY_INFORMATION_CSV = """address1,city,state,zip,country,phone,website,industry,industryKey,industryDisp,sector,sectorKey,sectorDisp,longBusinessSummary,fullTimeEmployees,companyOfficers,auditRisk,boardRisk,compensationRisk,shareHolderRightsRisk,overallRisk,governanceEpochDate,compensationAsOfEpochDate,irWebsite,executiveTeam,maxAge,priceHint,previousClose,open,dayLow,dayHigh,regularMarketPreviousClose,regularMarketOpen,regularMarketDayLow,regularMarketDayHigh,dividendRate,dividendYield,exDividendDate,payoutRatio,fiveYearAvgDividendYield,beta,trailingPE,forwardPE,volume,regularMarketVolume,averageVolume,averageVolume10days,averageDailyVolume10Day,bid,ask,bidSize,askSize,marketCap,nonDilutedMarketCap,fiftyTwoWeekLow,fiftyTwoWeekHigh,allTimeHigh,allTimeLow,priceToSalesTrailing12Months,fiftyDayAverage,twoHundredDayAverage,trailingAnnualDividendRate,trailingAnnualDividendYield,currency,tradeable,enterpriseValue,profitMargins,floatShares,sharesOutstanding,sharesShort,sharesShortPriorMonth,sharesShortPreviousMonthDate,dateShortInterest,sharesPercentSharesOut,heldPercentInsiders,heldPercentInstitutions,shortRatio,shortPercentOfFloat,impliedSharesOutstanding,bookValue,priceToBook,lastFiscalYearEnd,nextFiscalYearEnd,mostRecentQuarter,earningsQuarterlyGrowth,netIncomeToCommon,trailingEps,forwardEps,lastSplitFactor,lastSplitDate,enterpriseToRevenue,enterpriseToEbitda,52WeekChange,SandP52WeekChange,lastDividendValue,lastDividendDate,quoteType,currentPrice,targetHighPrice,targetLowPrice,targetMeanPrice,targetMedianPrice,recommendationMean,recommendationKey,numberOfAnalystOpinions,totalCash,totalCashPerShare,ebitda,totalDebt,quickRatio,currentRatio,totalRevenue,debtToEquity,revenuePerShare,returnOnAssets,returnOnEquity,grossProfits,freeCashflow,operatingCashflow,earningsGrowth,revenueGrowth,grossMargins,ebitdaMargins,operatingMargins,financialCurrency,symbol,language,region,typeDisp,quoteSourceName,triggerable,customPriceAlertConfidence,corporateActions,postMarketTime,regularMarketTime,exchange,messageBoardId,exchangeTimezoneName,exchangeTimezoneShortName,gmtOffSetMilliseconds,market,esgPopulated,regularMarketChangePercent,regularMarketPrice,marketState,shortName,longName,averageAnalystRating,cryptoTradeable,hasPrePostMarketData,firstTradeDateMilliseconds,postMarketChangePercent,postMarketPrice,postMarketChange,regularMarketChange,regularMarketDayRange,fullExchangeName,averageDailyVolume3Month,fiftyTwoWeekLowChange,fiftyTwoWeekLowChangePercent,fiftyTwoWeekRange,fiftyTwoWeekHighChange,fiftyTwoWeekHighChangePercent,fiftyTwoWeekChangePercent,dividendDate,earningsTimestamp,earningsTimestampStart,earningsTimestampEnd,earningsCallTimestampStart,earningsCallTimestampEnd,isEarningsDateEstimate,epsTrailingTwelveMonths,epsForward,epsCurrentYear,priceEpsCurrentYear,fiftyDayAverageChange,fiftyDayAverageChangePercent,twoHundredDayAverageChange,twoHundredDayAverageChangePercent,sourceInterval,exchangeDataDelayedBy,displayName,trailingPegRatio
One Apple Park Way,Cupertino,CA,95014,United States,(408) 996-1010,https://www.apple.com,Consumer Electronics,consumer-electronics,Consumer Electronics,Technology,technology,Technology,"Apple Inc. designs, manufactures, and markets smartphones, personal computers, tablets, wearables, and accessories worldwide. The company offers iPhone, a line of smartphones; Mac, a line of personal computers; iPad, a line of multi-purpose tablets; and wearables, home, and accessories comprising AirPods, Apple Vision Pro, Apple TV, Apple Watch, Beats products, and HomePod, as well as Apple branded and third-party accessories. It also provides AppleCare support and cloud services; and operates various platforms, including the App Store that allow customers to discover and download applications and digital content, such as books, music, video, games, and podcasts, as well as advertising services include third-party licensing arrangements and its own advertising platforms. In addition, the company offers various subscription-based services, such as Apple Arcade, a game subscription service; Apple Fitness+, a personalized fitness service; Apple Music, which offers users a curated listening experience with on-demand radio stations; Apple News+, a subscription news and magazine service; Apple TV, which offers exclusive original content and live sports; Apple Card, a co-branded credit card; and Apple Pay, a cashless payment service, as well as licenses its intellectual property. The company serves consumers, and small and mid-sized businesses; and the education, enterprise, and government markets. It distributes third-party applications for its products through the App Store. The company also sells its products through its retail and online stores, and direct sales force; and third-party cellular network carriers and resellers. The company was formerly known as Apple Computer, Inc. and changed its name to Apple Inc. in January 2007. Apple Inc. was founded in 1976 and is headquartered in Cupertino, California.",150000,"[{'maxAge': 1, 'name': 'Mr. Timothy D. Cook', 'age': 64, 'title': 'CEO & Director', 'yearBorn': 1961, 'fiscalYear': 2025, 'totalPay': 16759518, 'exercisedValue': 0, 'unexercisedValue': 0}, {'maxAge': 1, 'name': 'Mr. Kevan  Parekh', 'age': 53, 'title': 'Senior VP & CFO', 'yearBorn': 1972, 'fiscalYear': 2025, 'totalPay': 4034174, 'exercisedValue': 0, 'unexercisedValue': 0}, {'maxAge': 1, 'name': 'Mr. Sabih  Khan', 'age': 58, 'title': 'Senior VP & Chief Operating Officer', 'yearBorn': 1967, 'fiscalYear': 2025, 'totalPay': 5021905, 'exercisedValue': 0, 'unexercisedValue': 0}, {'maxAge': 1, 'name': ""Ms. Deirdre  O'Brien"", 'age': 58, 'title': 'Senior Vice President of Retail & People', 'yearBorn': 1967, 'fiscalYear': 2025, 'totalPay': 5037867, 'exercisedValue': 0, 'unexercisedValue': 0}, {'maxAge': 1, 'name': 'Ms. Katherine L. Adams', 'age': 61, 'title': 'Senior VP of Government Affairs & Secretary', 'yearBorn': 1964, 'fiscalYear': 2025, 'totalPay': 5022482, 'exercisedValue': 0, 'unexercisedValue': 0}, {'maxAge': 1, 'name': 'Mr. Ben  Borders', 'age': 44, 'title': 'Principal Accounting Officer', 'yearBorn': 1981, 'fiscalYear': 2025, 'exercisedValue': 0, 'unexercisedValue': 0}, {'maxAge': 1, 'name': 'Suhasini  Chandramouli', 'title': 'Director of Investor Relations', 'fiscalYear': 2025, 'exercisedValue': 0, 'unexercisedValue': 0}, {'maxAge': 1, 'name': 'Ms. Jennifer G. Newstead J.D.', 'age': 54, 'title': 'Senior VP & General Counsel', 'yearBorn': 1971, 'fiscalYear': 2025, 'exercisedValue': 0, 'unexercisedValue': 0}, {'maxAge': 1, 'name': 'Ms. Kristin Huguet Quayle', 'title': 'Vice President of Worldwide Communications', 'fiscalYear': 2025, 'exercisedValue': 0, 'unexercisedValue': 0}, {'maxAge': 1, 'name': 'Mr. Greg  Joswiak', 'title': 'Senior Vice President of Worldwide Marketing', 'fiscalYear': 2025, 'exercisedValue': 0, 'unexercisedValue': 0}]",2,1,7,1,1,1772323200,1767139200,http://investor.apple.com/,[],86400,2,248.96,248.11,246.0,249.1999,248.96,248.11,246.0,249.1999,1.04,0.42,1770595200,0.1304,0.52,1.116,31.351456,26.605259,87981315,87981315,46303626,39607800,39607800,235.77,248.06,1,1,3644938780672,3640775908600,169.21,288.62,288.62,0.049107,8.367301,261.13,246.82304,1.03,0.0041372105,USD,False,3664377806848,0.27037,14656182062,14681140000,129553812,116854414,1769731200,1772150400,0.0088,0.016390001,0.65264,2.41,0.0088,14697926000,5.998,41.345448,1758931200,1790467200,1766793600,0.159,117776998400,7.91,9.32109,4:1,1598832000,8.412,23.966,0.123499274,0.12811458,0.26,1770595200,EQUITY,247.99,350.0,205.0,295.43536,300.0,1.89583,buy,41,66907000832,4.557,152901992448,90509000704,0.845,0.974,435617005568,102.63,29.305,0.24377,1.5202099,206157004800,106312753152,135471996928,0.183,0.157,0.47325,0.35099998,0.35374,USD,AAPL,en-US,US,Equity,Nasdaq Real Time Price,True,HIGH,[],1774051191,1774036800,NMS,finmb_24937,America/New_York,EDT,-14400000,us_market,False,-0.389621,247.99,CLOSED,Apple Inc.,Apple Inc.,1.9 - Buy,False,True,345479400000,0.72986716,249.8,1.8099976,-0.970001,246.0 - 249.1999,NasdaqGS,46303626,78.78,0.4655753,169.21 - 288.62,-40.62999,-0.1407733,12.349928,1770854400,1769720400,1777579200,1777579200,1769724000,1769724000,True,7.91,9.32109,8.51182,29.13478,-13.139999,-0.05031976,1.1669617,0.0047279284,15,0,Apple,2.2029"""

INCOME_STATEMENT_CSV = """date,Tax Effect Of Unusual Items,Tax Rate For Calcs,Normalized EBITDA,Net Income From Continuing Operation Net Minority Interest,Reconciled Depreciation,Reconciled Cost Of Revenue,EBITDA,EBIT,Net Interest Income,Interest Expense,Interest Income,Normalized Income,Net Income From Continuing And Discontinued Operation,Total Expenses,Total Operating Income As Reported,Diluted Average Shares,Basic Average Shares,Diluted EPS,Basic EPS,Diluted NI Availto Com Stockholders,Net Income Common Stockholders,Net Income,Net Income Including Noncontrolling Interests,Net Income Continuous Operations,Tax Provision,Pretax Income,Other Income Expense,Other Non Operating Income Expenses,Net Non Operating Interest Income Expense,Interest Expense Non Operating,Interest Income Non Operating,Operating Income,Operating Expense,Research And Development,Selling General And Administration,Gross Profit,Cost Of Revenue,Total Revenue,Operating Revenue
2025-09-30,0.0,0.156,144748000000.0,112010000000.0,11698000000.0,220960000000.0,144748000000.0,133050000000.0,,,,112010000000.0,112010000000.0,283111000000.0,133050000000.0,15004697000.0,14948500000.0,7.46,7.49,112010000000.0,112010000000.0,112010000000.0,112010000000.0,112010000000.0,20719000000.0,132729000000.0,-321000000.0,-321000000.0,,,,133050000000.0,62151000000.0,34550000000.0,27601000000.0,195201000000.0,220960000000.0,416161000000.0,416161000000.0
2024-09-30,0.0,0.241,134661000000.0,93736000000.0,11445000000.0,210352000000.0,134661000000.0,123216000000.0,,,,93736000000.0,93736000000.0,267819000000.0,123216000000.0,15408095000.0,15343783000.0,6.08,6.11,93736000000.0,93736000000.0,93736000000.0,93736000000.0,93736000000.0,29749000000.0,123485000000.0,269000000.0,269000000.0,,,,123216000000.0,57467000000.0,31370000000.0,26097000000.0,180683000000.0,210352000000.0,391035000000.0,391035000000.0
2023-09-30,0.0,0.147,125820000000.0,96995000000.0,11519000000.0,214137000000.0,125820000000.0,114301000000.0,-183000000.0,3933000000.0,3750000000.0,96995000000.0,96995000000.0,268984000000.0,114301000000.0,15812547000.0,15744231000.0,6.13,6.16,96995000000.0,96995000000.0,96995000000.0,96995000000.0,96995000000.0,16741000000.0,113736000000.0,-565000000.0,-565000000.0,-183000000.0,3933000000.0,3750000000.0,114301000000.0,54847000000.0,29915000000.0,24932000000.0,169148000000.0,214137000000.0,383285000000.0,383285000000.0
2022-09-30,0.0,0.162,130541000000.0,99803000000.0,11104000000.0,223546000000.0,130541000000.0,119437000000.0,-106000000.0,2931000000.0,2825000000.0,99803000000.0,99803000000.0,274891000000.0,119437000000.0,16325819000.0,16215963000.0,6.11,6.15,99803000000.0,99803000000.0,99803000000.0,99803000000.0,99803000000.0,19300000000.0,119103000000.0,-334000000.0,-334000000.0,-106000000.0,2931000000.0,2825000000.0,119437000000.0,51345000000.0,26251000000.0,25094000000.0,170782000000.0,223546000000.0,394328000000.0,394328000000.0
2021-09-30,,,,,,,,,198000000.0,2645000000.0,2843000000.0,,,,,,,,,,,,,,,,,,198000000.0,2645000000.0,2843000000.0,,,,,,,,"""

BALANCE_SHEET_CSV = """date,Treasury Shares Number,Ordinary Shares Number,Share Issued,Net Debt,Total Debt,Tangible Book Value,Invested Capital,Working Capital,Net Tangible Assets,Capital Lease Obligations,Common Stock Equity,Total Capitalization,Total Equity Gross Minority Interest,Stockholders Equity,Gains Losses Not Affecting Retained Earnings,Other Equity Adjustments,Retained Earnings,Capital Stock,Common Stock,Total Liabilities Net Minority Interest,Total Non Current Liabilities Net Minority Interest,Other Non Current Liabilities,Tradeand Other Payables Non Current,Long Term Debt And Capital Lease Obligation,Long Term Capital Lease Obligation,Long Term Debt,Current Liabilities,Other Current Liabilities,Current Deferred Liabilities,Current Deferred Revenue,Current Debt And Capital Lease Obligation,Current Capital Lease Obligation,Current Debt,Other Current Borrowings,Commercial Paper,Payables And Accrued Expenses,Current Accrued Expenses,Payables,Total Tax Payable,Income Tax Payable,Accounts Payable,Total Assets,Total Non Current Assets,Other Non Current Assets,Non Current Deferred Assets,Non Current Deferred Taxes Assets,Investments And Advances,Other Investments,Investmentin Financial Assets,Available For Sale Securities,Net PPE,Accumulated Depreciation,Gross PPE,Leases,Other Properties,Machinery Furniture Equipment,Land And Improvements,Properties,Current Assets,Other Current Assets,Inventory,Receivables,Other Receivables,Accounts Receivable,Cash Cash Equivalents And Short Term Investments,Other Short Term Investments,Cash And Cash Equivalents,Cash Equivalents,Cash Financial
2025-09-30,,14773260000.0,14773260000.0,62723000000.0,98657000000.0,73733000000.0,172390000000.0,-17674000000.0,73733000000.0,,73733000000.0,152061000000.0,73733000000.0,73733000000.0,-5571000000.0,-5571000000.0,-14264000000.0,93568000000.0,93568000000.0,285508000000.0,119877000000.0,41549000000.0,,78328000000.0,,78328000000.0,165631000000.0,44452000000.0,9055000000.0,9055000000.0,20329000000.0,,20329000000.0,12350000000.0,7979000000.0,91795000000.0,8919000000.0,82876000000.0,13016000000.0,13016000000.0,69860000000.0,359241000000.0,211284000000.0,62950000000.0,20777000000.0,20777000000.0,77723000000.0,,77723000000.0,77723000000.0,49834000000.0,-76014000000.0,125848000000.0,15091000000.0,,83420000000.0,27337000000.0,0.0,147957000000.0,14585000000.0,5718000000.0,72957000000.0,33180000000.0,39777000000.0,54697000000.0,18763000000.0,35934000000.0,7667000000.0,28267000000.0
2024-09-30,,15116786000.0,15116786000.0,76686000000.0,106629000000.0,56950000000.0,163579000000.0,-23405000000.0,56950000000.0,,56950000000.0,142700000000.0,56950000000.0,56950000000.0,-7172000000.0,-7172000000.0,-19154000000.0,83276000000.0,83276000000.0,308030000000.0,131638000000.0,45888000000.0,9254000000.0,85750000000.0,,85750000000.0,176392000000.0,44024000000.0,8249000000.0,8249000000.0,20879000000.0,,20879000000.0,10912000000.0,9967000000.0,103240000000.0,,95561000000.0,26601000000.0,26601000000.0,68960000000.0,364980000000.0,211993000000.0,55335000000.0,19499000000.0,19499000000.0,91479000000.0,,91479000000.0,91479000000.0,45680000000.0,-73448000000.0,119128000000.0,14233000000.0,,80205000000.0,24690000000.0,0.0,152987000000.0,14287000000.0,7286000000.0,66243000000.0,32833000000.0,33410000000.0,65171000000.0,35228000000.0,29943000000.0,2744000000.0,27199000000.0
2023-09-30,0.0,15550061000.0,15550061000.0,81123000000.0,111088000000.0,62146000000.0,173234000000.0,-1742000000.0,62146000000.0,12842000000.0,62146000000.0,157427000000.0,62146000000.0,62146000000.0,-11452000000.0,-11452000000.0,-214000000.0,73812000000.0,73812000000.0,290437000000.0,145129000000.0,34391000000.0,15457000000.0,95281000000.0,11267000000.0,95281000000.0,145308000000.0,50010000000.0,8061000000.0,8061000000.0,15807000000.0,1575000000.0,15807000000.0,9822000000.0,5985000000.0,71430000000.0,,71430000000.0,8819000000.0,8819000000.0,62611000000.0,352583000000.0,209017000000.0,46906000000.0,17852000000.0,17852000000.0,100544000000.0,,100544000000.0,100544000000.0,43715000000.0,-70884000000.0,114599000000.0,12839000000.0,10661000000.0,78314000000.0,23446000000.0,0.0,143566000000.0,14695000000.0,6331000000.0,60985000000.0,31477000000.0,29508000000.0,61555000000.0,31590000000.0,29965000000.0,1606000000.0,28359000000.0
2022-09-30,,15943425000.0,15943425000.0,96423000000.0,132480000000.0,50672000000.0,170741000000.0,-18577000000.0,50672000000.0,12411000000.0,50672000000.0,149631000000.0,50672000000.0,50672000000.0,-11109000000.0,-11109000000.0,-3068000000.0,64849000000.0,64849000000.0,302083000000.0,148101000000.0,21737000000.0,16657000000.0,109707000000.0,10748000000.0,98959000000.0,153982000000.0,52630000000.0,7912000000.0,7912000000.0,22773000000.0,1663000000.0,21110000000.0,11128000000.0,9982000000.0,70667000000.0,,70667000000.0,6552000000.0,6552000000.0,64115000000.0,352755000000.0,217350000000.0,39053000000.0,15375000000.0,15375000000.0,120805000000.0,120805000000.0,120805000000.0,120805000000.0,42117000000.0,-72340000000.0,114457000000.0,11271000000.0,10417000000.0,81060000000.0,22126000000.0,0.0,135405000000.0,21223000000.0,4946000000.0,60932000000.0,32748000000.0,28184000000.0,48304000000.0,24658000000.0,23646000000.0,5100000000.0,18546000000.0
2021-09-30,,,,,,,,,,11803000000.0,,,,,,,,,,,,,24689000000.0,,10275000000.0,,,,,,,1528000000.0,,,,,,,,,,,,,,,,127877000000.0,,,,,,,10087000000.0,,,,,,,,,,,,,,
"""

CASHFLOW_CSV = """date,Free Cash Flow,Repurchase Of Capital Stock,Repayment Of Debt,Issuance Of Debt,Issuance Of Capital Stock,Capital Expenditure,Interest Paid Supplemental Data,Income Tax Paid Supplemental Data,End Cash Position,Beginning Cash Position,Changes In Cash,Financing Cash Flow,Cash Flow From Continuing Financing Activities,Net Other Financing Charges,Cash Dividends Paid,Common Stock Dividend Paid,Net Common Stock Issuance,Common Stock Payments,Common Stock Issuance,Net Issuance Payments Of Debt,Net Short Term Debt Issuance,Net Long Term Debt Issuance,Long Term Debt Payments,Long Term Debt Issuance,Investing Cash Flow,Cash Flow From Continuing Investing Activities,Net Other Investing Changes,Net Investment Purchase And Sale,Sale Of Investment,Purchase Of Investment,Net Business Purchase And Sale,Purchase Of Business,Net PPE Purchase And Sale,Purchase Of PPE,Operating Cash Flow,Cash Flow From Continuing Operating Activities,Change In Working Capital,Change In Other Working Capital,Change In Other Current Liabilities,Change In Other Current Assets,Change In Payables And Accrued Expense,Change In Payable,Change In Account Payable,Change In Inventory,Change In Receivables,Changes In Account Receivables,Other Non Cash Items,Stock Based Compensation,Deferred Tax,Deferred Income Tax,Depreciation Amortization Depletion,Depreciation And Amortization,Net Income From Continuing Operations
2025-09-30,98767000000.0,-90711000000.0,-10932000000.0,4481000000.0,,-12715000000.0,,43369000000.0,35934000000.0,29943000000.0,5991000000.0,-120686000000.0,-120686000000.0,-6071000000.0,-15421000000.0,-15421000000.0,-90711000000.0,-90711000000.0,,-8483000000.0,-2032000000.0,-6451000000.0,-10932000000.0,4481000000.0,15195000000.0,15195000000.0,-1480000000.0,29390000000.0,53797000000.0,-24407000000.0,,,-12715000000.0,-12715000000.0,111482000000.0,111482000000.0,-25000000000.0,,-11076000000.0,-9197000000.0,902000000.0,902000000.0,902000000.0,1400000000.0,-7029000000.0,-6682000000.0,-89000000.0,12863000000.0,,,11698000000.0,11698000000.0,112010000000.0
2024-09-30,108807000000.0,-94949000000.0,-9958000000.0,0.0,,-9447000000.0,,26102000000.0,29943000000.0,30737000000.0,-794000000.0,-121983000000.0,-121983000000.0,-5802000000.0,-15234000000.0,-15234000000.0,-94949000000.0,-94949000000.0,,-5998000000.0,3960000000.0,-9958000000.0,-9958000000.0,0.0,2935000000.0,2935000000.0,-1308000000.0,13690000000.0,62346000000.0,-48656000000.0,,,-9447000000.0,-9447000000.0,118254000000.0,118254000000.0,3651000000.0,,15552000000.0,-11731000000.0,6020000000.0,6020000000.0,6020000000.0,-1046000000.0,-5144000000.0,-3788000000.0,-2266000000.0,11688000000.0,,,11445000000.0,11445000000.0,93736000000.0
2023-09-30,99584000000.0,-77550000000.0,-11151000000.0,5228000000.0,,-10959000000.0,3803000000.0,18679000000.0,30737000000.0,24977000000.0,5760000000.0,-108488000000.0,-108488000000.0,-6012000000.0,-15025000000.0,-15025000000.0,-77550000000.0,-77550000000.0,,-9901000000.0,-3978000000.0,-5923000000.0,-11151000000.0,5228000000.0,3705000000.0,3705000000.0,-1337000000.0,16001000000.0,45514000000.0,-29513000000.0,,,-10959000000.0,-10959000000.0,110543000000.0,110543000000.0,-6577000000.0,,3031000000.0,-5684000000.0,-1889000000.0,-1889000000.0,-1889000000.0,-1618000000.0,-417000000.0,-1688000000.0,-2227000000.0,10833000000.0,,,11519000000.0,11519000000.0,96995000000.0
2022-09-30,111443000000.0,-89402000000.0,-9543000000.0,5465000000.0,,-10708000000.0,2865000000.0,19573000000.0,24977000000.0,35929000000.0,-10952000000.0,-110749000000.0,-110749000000.0,-6383000000.0,-14841000000.0,-14841000000.0,-89402000000.0,-89402000000.0,,-123000000.0,3955000000.0,-4078000000.0,-9543000000.0,5465000000.0,-22354000000.0,-22354000000.0,-2086000000.0,-9560000000.0,67363000000.0,-76923000000.0,-306000000.0,-306000000.0,-10708000000.0,-10708000000.0,122151000000.0,122151000000.0,1200000000.0,478000000.0,6110000000.0,-6499000000.0,9448000000.0,9448000000.0,9448000000.0,1484000000.0,-9343000000.0,-1823000000.0,1006000000.0,9038000000.0,895000000.0,895000000.0,11104000000.0,11104000000.0,99803000000.0
2021-09-30,,,,,1105000000.0,,2687000000.0,,,,,,,,,,,,1105000000.0,,,,,,,,,,,,-33000000.0,-33000000.0,,,,,,1676000000.0,,,,,,,,,,,-4774000000.0,-4774000000.0,,,
"""

NEWS_CSV = """title,summary,description,url
Is Apple Stock Going to $500? Here's What Has to Happen.,"After an impressive 953% trailing-10-year total return, investors are ready to tackle the next milestone.",,https://www.fool.com/investing/2026/03/21/apple-stock-going-to-500-what-has-to-happen/
Nvidia's headquarters: An ode to space and 3D rendering,"Nvidia is the world's largest publicly traded company. As such, it boasts state-of-the-art, futuristic office space that highlights its status as a Silicon Valley tech giant. While Apple has a ring-shaped headquarters, known as Apple Park, Nvidia's headquarters are polygonal in shape, which ...",,https://www.thestreet.com/technology/nvidia-headquarters
How Apple Is Winning China's Brutal Smartphone Price War,"China's smartphone sales fell 4% year over year in the first nine weeks of 2026, according to Counterpoint Research's China Weekly Smartphone Sell-Out Tracker. The decline reflects soft consumer demand and underwhelming Lunar New Year promotions. Government subsidies introduced early in the year have had limited impact so far. While February promotions lifted sales from January levels, rising memory prices constrained discounts. As a result, sales during the holiday period and the preceding thre",,https://finance.yahoo.com/markets/stocks/articles/apple-winning-chinas-brutal-smartphone-143107839.html
Apple App Rules On AI Coding And China Scrutiny Shape Investor Focus,"Apple is reportedly blocking updates to certain AI powered vibe coding apps, citing App Store policy violations. The move raises questions about how Apple applies its rules to third party tools that touch software development and app distribution. At the same time, Apple is under increased regulatory scrutiny in China after cutting its App Store commission rate and facing calls to further ease restrictions. For investors watching NasdaqGS:AAPL, these app policy decisions come against a...",,https://finance.yahoo.com/markets/stocks/articles/apple-app-rules-ai-coding-010635727.html
Warren Buffett Bought 8 Million Shares of This Oil Giant and $100 Oil Proves Him Right,"Berkshire Hathaway quietly added to its Chevron stake before crude pushed back toward $100, and the timing is hard to ignore. The move highlights what Buffett has long favored in energy: durability, disciplined shareholder returns, and upside when the commodity cycle turns.",,https://www.fool.com/investing/2026/03/20/warren-buffett-bought-8-million-shares-of-this-oil/
"The Dealmaking 3: MLB & Adobe Expanding Partnership, AI in Pickleball, Apple TV's Deal with F1","Watch The Dealmaking 3 of the Week: This week of The Dealmaking 3 with “The Sports Professor” Rick Horrow features MLB and Adobe Inc. (Nasdaq: ADBE) expanding their 2021 partnership to enhance digital fans experiences and content delivery, PlaySight and Microsoft Corporation (Nasdaq: MSFT) designing a generative AI analysis tool for pickleball, and Apple Inc. (Nasdaq: […] The post The Dealmaking 3: MLB & Adobe Expanding Partnership, AI in Pickleball, Apple TV's Deal with F1 appeared first on Cor",,https://finance.yahoo.com/markets/stocks/articles/dealmaking-3-mlb-adobe-expanding-210232252.html
Apple's Latest Launch Was 'Best' Ever for New Mac Customers. What It Means for the Stock.,"'I view the recent launches of Mac products as a major success for Apple near-term and medium-term,' Oppenheimer analyst Martin Yang said.",,https://www.barrons.com/articles/apple-launch-best-ever-new-mac-customers-821919b0?siteid=yhoof2&yptr=yahoo
Here's Why Apple (AAPL) Could Be The Best Tech Stock to Buy Now According to Warren Buffett,We just covered the 10 Best Stocks to Buy Now According to Warren Buffett. Apple Inc. (NASDAQ:AAPL) ranks #1 (see the 5 best stocks to buy now here). Apple Inc. (NASDAQ:AAPL) remains the biggest holding of Berkshire despite the fund decreasing its stake in the iPhone maker over the past few quarters. Wall Street was extremely […],,https://finance.yahoo.com/markets/stocks/articles/why-apple-aapl-could-best-201647130.html
"Amazon is building a phone again, and this one is different","More than a decade after one of Silicon Valley's most embarrassing product failures, Amazon (AMZN) is back in the smartphone business. And this time, the bet is built on something the Fire Phone never had: a genuinely compelling reason to exist. Amazon is developing a new phone internally codenamed ...",,https://www.thestreet.com/technology/amazon-is-building-a-phone-again-and-this-one-is-different
"""


# =================================================
# Markdown Styles
# =================================================
st.markdown(
    """
<style>
    /* Global Styles */
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 3rem;
    }
    
    /* Card Styles */
    .stCard {
        background-color: #262730;
        border-radius: 0.5rem;
        padding: 1.5rem;
        border: 1px solid #41424C;
        height: 100%;
    }
    
    /* Header Styles */
    .company-header-container {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        padding-bottom: 2rem;
        border-bottom: 1px solid #41424C;
        margin-bottom: 2rem;
    }
    
    .ticker-pill {
        background-color: rgba(0, 122, 255, 0.2);
        color: #0d8cff;
        padding: 0.2rem 0.6rem;
        border-radius: 4px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
        display: inline-block;
    }
    
    .company-title {
        font-size: 3rem;
        font-weight: 800;
        margin: 0;
        padding: 0;
        line-height: 1.2;
    }
    
    .company-subtitle {
        color: #9CA3AF;
        margin-top: 0.5rem;
        font-size: 1rem;
    }
    
    .price-large {
        font-size: 3.5rem;
        font-weight: 700;
        text-align: right;
    }
    
    .price-change-container {
        text-align: right;
        font-size: 1.2rem;
        font-weight: 500;
    }
    
    /* Metric Item Styles */
    .metric-item {
        margin-bottom: 1rem;
    }
    
    .metric-label {
        font-size: 0.85rem;
        color: #9CA3AF;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    .metric-value-large {
        font-size: 1.8rem;
        font-weight: 600;
        color: #FFFFFF;
    }

    /* Analyst Badge */
    .analyst-badge {
        padding: 0.4rem 1rem;
        border-radius: 9999px;
        font-weight: 600;
        text-align: center;
        width: fit-content;
    }
    
    .badge-buy-strong { background-color: rgba(52, 199, 89, 0.2); color: #4ade80; }
    .badge-buy { background-color: rgba(52, 199, 89, 0.15); color: #4ade80; }
    .badge-hold { background-color: rgba(255, 149, 0, 0.15); color: #fbbf24; }
    .badge-sell { background-color: rgba(255, 59, 48, 0.15); color: #f87171; }
    
    /* News Item */
    .news-item {
        padding: 1.5rem;
        border-bottom: 1px solid #41424C;
        transition: background-color 0.2s;
        border-radius: 8px;
    }
    
    .news-item:hover {
        background-color: rgba(255, 255, 255, 0.03);
    }
    
    .news-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: #60A5FA;
        margin-bottom: 0.5rem;
        text-decoration: none;
        display: block;
    }
    
     .news-title:hover {
        text-decoration: underline;
    }
    
    .news-meta {
        font-size: 0.8rem;
        color: #9CA3AF;
    }
</style>
""",
    unsafe_allow_html=True,
)


@st.cache_data(ttl=3600)
def load_data():
    """Load all financial data from static strings."""
    company_information = pd.read_csv(io.StringIO(COMPANY_INFORMATION_CSV))
    income_statement = pd.read_csv(io.StringIO(INCOME_STATEMENT_CSV))
    balance_sheet = pd.read_csv(io.StringIO(BALANCE_SHEET_CSV))
    cashflow = pd.read_csv(io.StringIO(CASHFLOW_CSV))
    news = pd.read_csv(io.StringIO(NEWS_CSV))

    return company_information, income_statement, balance_sheet, cashflow, news


def format_number(num, suffix=""):
    """Format large numbers in a readable way."""
    if pd.isna(num) or num == 0:
        return "N/A"

    abs_num = abs(num)
    if abs_num >= 1e12:
        return f"${num / 1e12:.2f}T{suffix}"
    elif abs_num >= 1e9:
        return f"${num / 1e9:.2f}B{suffix}"
    elif abs_num >= 1e6:
        return f"${num / 1e6:.2f}M{suffix}"
    elif abs_num >= 1e3:
        return f"${num / 1e3:.2f}K{suffix}"
    else:
        return f"${num:,.2f}{suffix}"


def format_percentage(val):
    """Format percentage values."""
    if pd.isna(val):
        return "N/A"
    return f"{val * 100:.2f}%"


def get_recommendation_badge(rating):
    """Get badge class based on recommendation rating."""
    if rating <= 1.5:
        return "badge-buy-strong", "Strong Buy"
    elif rating <= 2.5:
        return "badge-buy", "Buy"
    elif rating <= 3.5:
        return "badge-hold", "Hold"
    elif rating <= 4.5:
        return "badge-sell", "Sell"
    else:
        return "badge-sell", "Strong Sell"


def card_container(content):
    st.markdown(f'<div class="stCard">{content}</div>', unsafe_allow_html=True)


def profile():
    # Load data
    company_information, income_statement, balance_sheet, cashflow, news = load_data()

    # Extract key metrics
    current_price = company_information["currentPrice"].values[0]
    previous_close = company_information["previousClose"].values[0]
    price_change = current_price - previous_close
    price_change_pct = (price_change / previous_close) * 100
    market_cap = company_information["marketCap"].values[0]
    revenue = company_information["totalRevenue"].values[0]
    net_income = company_information["netIncomeToCommon"].values[0]
    pe_trailing = company_information["trailingPE"].values[0]
    dividend_yield = company_information["dividendYield"].values[0]
    beta = company_information["beta"].values[0]
    profit_margin = company_information["profitMargins"].values[0]
    roe = company_information["returnOnEquity"].values[0]
    gross_margin = company_information["grossMargins"].values[0]
    operating_margin = company_information["operatingMargins"].values[0]
    target_mean = company_information["targetMeanPrice"].values[0]
    target_high = company_information["targetHighPrice"].values[0]
    target_low = company_information["targetLowPrice"].values[0]
    rec_mean = company_information["recommendationMean"].values[0]
    num_analysts = company_information["numberOfAnalystOpinions"].values[0]

    # Header section
    price_color = "#34C759" if price_change >= 0 else "#FF3B30"
    st.markdown(
        f"""
    <div class="company-header-container">
        <div>
            <span class="ticker-pill">NASDAQ: AAPL</span>
            <h1 class="company-title">Apple Inc.</h1>
            <div class="company-subtitle">Consumer Electronics • Technology Sector • Cupertino, CA</div>
        </div>
        <div style="text-align: right;">
            <div class="price-large">${current_price:.2f}</div>
            <div class="price-change-container" style="color: {price_color};">
                {price_change:+.2f} ({price_change_pct:+.2f}%)
            </div>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Main Tabs
    tab_overview, tab_financials, tab_analysis, tab_news = st.tabs(
        ["Overview", "Financials", "Analysis", "News"]
    )

    with tab_overview:
        col1, col2 = st.columns([2, 1])

        with col1:
            st.subheader("About")
            st.write(company_information["longBusinessSummary"].values[0])

            st.subheader("Key Metrics")
            k_col1, k_col2, k_col3 = st.columns(3)
            with k_col1:
                st.metric("Market Cap", format_number(market_cap))
                st.metric("Revenue (TTM)", format_number(revenue))
            with k_col2:
                st.metric("P/E Ratio", f"{pe_trailing:.2f}")
                st.metric("Net Income", format_number(net_income))
            with k_col3:
                st.metric("Dividend Yield", f"{dividend_yield:.2f}%")
                st.metric("Beta", f"{beta:.2f}")

        with col2:
            st.subheader("Details")
            employees = company_information["fullTimeEmployees"].values[0]
            website = company_information["website"].values[0]

            detail_data = {
                "Employees": f"{employees:,.0f}",
                "Sector": "Technology",
                "Industry": "Consumer Electronics",
                "Website": website,
            }

            for k, v in detail_data.items():
                st.markdown(f"**{k}**")
                if "http" in v:
                    st.markdown(f"[{v}]({v})")
                else:
                    st.markdown(f"{v}")
                st.markdown("---")
            st.markdown("</div>", unsafe_allow_html=True)

    with tab_financials:
        st.subheader("Profitability & Margins")
        m_col1, m_col2, m_col3, m_col4 = st.columns(4)
        m_col1.metric("Gross Margin", format_percentage(gross_margin))
        m_col2.metric("Operating Margin", format_percentage(operating_margin))
        m_col3.metric("Profit Margin", format_percentage(profit_margin))
        m_col4.metric("ROE", format_percentage(roe))

        st.divider()

        st.subheader("Balance Sheet Highlights")
        b_col1, b_col2, b_col3 = st.columns(3)

        total_assets = balance_sheet["Total Assets"].iloc[0]
        total_debt = balance_sheet["Total Debt"].iloc[0]
        cash = balance_sheet["Cash And Cash Equivalents"].iloc[0]

        b_col1.metric("Total Assets", format_number(total_assets))
        b_col2.metric("Total Debt", format_number(total_debt))
        b_col3.metric("Cash & Equivalents", format_number(cash))

        st.divider()

        st.subheader("Cash Flow")
        c_col1, c_col2, c_col3 = st.columns(3)
        operating_cf = cashflow["Operating Cash Flow"].iloc[0]
        free_cf = cashflow["Free Cash Flow"].iloc[0]
        capex = abs(cashflow["Capital Expenditure"].iloc[0])

        c_col1.metric("Operating Cash Flow", format_number(operating_cf))
        c_col2.metric("Free Cash Flow", format_number(free_cf))
        c_col3.metric("Capital Expenditure", format_number(capex))

    with tab_analysis:
        st.subheader("Analyst Consensus")
        rec_badge_class, rec_text = get_recommendation_badge(rec_mean)
        upside = ((target_mean - current_price) / current_price) * 100

        st.markdown(
            f"""
        <div class="stCard" style="display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center;">
            <div style="font-size: 1.2rem; margin-bottom: 1rem;">Recommendation</div>
            <div class="analyst-badge {rec_badge_class}" style="font-size: 1.5rem; margin-bottom: 0.5rem;">{rec_text}</div>
            <div style="color: #9CA3AF;">Score: {rec_mean:.2f} / 5.0</div>
            <div style="color: #9CA3AF; font-size: 0.8rem; margin-top: 0.5rem;">Based on {int(num_analysts)} analysts</div>
        </div>
        <br>
        <div class="stCard" style="text-align: center;">
            <div style="font-size: 1.2rem; margin-bottom: 1rem;">Price Target</div>
            <div style="font-size: 2.5rem; font-weight: 700;">${target_mean:.2f}</div>
            <div style="color: {"#34C759" if upside > 0 else "#FF3B30"}; font-size: 1.2rem; font-weight: 600;">{upside:+.1f}% Upside</div>
            <div style="margin-top: 1.5rem; display: flex; justify-content: space-between; padding: 0 20%;">
                <div>
                    <div style="font-size: 0.8rem; color: #9CA3AF;">Low</div>
                    <div style="font-weight: 600;">${target_low:.0f}</div>
                </div>
                <div>
                    <div style="font-size: 0.8rem; color: #9CA3AF;">High</div>
                    <div style="font-weight: 600;">${target_high:.0f}</div>
                </div>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with tab_news:
        st.subheader("Latest News")
        for _, row in news.head(10).iterrows():
            title = row["title"]
            summary = row["summary"] if pd.notna(row["summary"]) else ""
            url = row["url"]

            st.markdown(
                f"""
            <div class="news-item">
                <a href="{url}" target="_blank" class="news-title">{title}</a>
                <div class="news-meta">{summary[:260]}{"..." if len(summary) > 260 else ""}</div>
            </div>
            """,
                unsafe_allow_html=True,
            )

    # Footer
    st.markdown(
        """
    <div style="margin-top: 4rem; padding: 2rem; border-top: 1px solid #41424C; text-align: center; color: #6B7280; font-size: 0.8rem;">
        <p>Data sourced from Yahoo Finance</p>
        <p>This dashboard is for informational purposes only and does not constitute investment advice.</p>
    </div>
    """,
        unsafe_allow_html=True,
    )


profile()
