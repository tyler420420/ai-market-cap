$action = New-ScheduledTaskAction -Execute "cmd" -Argument "/c C:\Users\Tyler_AI\.mavis\sessions\mvs_41a119d03ae849d59a2cdecd57e77d10\workspace\run_tracker.bat"
$trigger = New-ScheduledTaskTrigger -Daily -At "06:35AM"
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable
$existing = Get-ScheduledTask -TaskName "AI Market Cap Tracker" -ErrorAction SilentlyContinue
if ($existing) { Unregister-ScheduledTask -TaskName "AI Market Cap Tracker" -Confirm:$false }
Register-ScheduledTask -TaskName "AI Market Cap Tracker" -Action $action -Trigger $trigger -Settings $settings -Description "AI Market Cap Tracker - Twitter bot with auto-restart"