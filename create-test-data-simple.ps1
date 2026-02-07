# Simple Test Data Creation
# Creates one project and one task to test the system

Write-Host "Creating simple test data..." -ForegroundColor Cyan

# Check backend
try {
    $null = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method GET -ErrorAction Stop
    Write-Host "Backend is running" -ForegroundColor Green
} catch {
    Write-Host "Error: Backend not running" -ForegroundColor Red
    exit 1
}

# Create a simple project
Write-Host "Creating test project..." -ForegroundColor Yellow

$projectData = @{
    title = "Test Project"
    description = "A simple test project"
    status = "active"
    priority = 2
} | ConvertTo-Json

Write-Host "Sending data: $projectData" -ForegroundColor Gray

try {
    $project = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/projects" `
        -Method POST `
        -ContentType "application/json" `
        -Body $projectData `
        -ErrorAction Stop

    Write-Host "Success! Created project ID: $($project.id)" -ForegroundColor Green
    Write-Host "Project title: $($project.title)" -ForegroundColor Green

    # Create a task
    Write-Host ""
    Write-Host "Creating test task..." -ForegroundColor Yellow

    $taskData = @{
        title = "Test Task"
        description = "A simple test task"
        project_id = $project.id
        is_next_action = $true
        status = "pending"
    } | ConvertTo-Json

    $task = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/tasks" `
        -Method POST `
        -ContentType "application/json" `
        -Body $taskData `
        -ErrorAction Stop

    Write-Host "Success! Created task ID: $($task.id)" -ForegroundColor Green
    Write-Host "Task title: $($task.title)" -ForegroundColor Green

    Write-Host ""
    Write-Host "Test data created! Refresh http://localhost:5173" -ForegroundColor Cyan

} catch {
    Write-Host "Error creating data:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    if ($_.ErrorDetails) {
        Write-Host "Details: $($_.ErrorDetails.Message)" -ForegroundColor Red
    }
}
