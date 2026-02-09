# Conduital - Test Data Creation Script
# Creates sample projects and tasks for testing the frontend

Write-Host "================================" -ForegroundColor Cyan
Write-Host "Conduital - Test Data Creator" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Check if backend is running
try {
    $health = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method GET -ErrorAction Stop
    Write-Host "Backend is running" -ForegroundColor Green
} catch {
    Write-Host "Error: Backend is not running at http://localhost:8000" -ForegroundColor Red
    Write-Host "Please start the backend first:" -ForegroundColor Yellow
    Write-Host "  cd backend" -ForegroundColor Yellow
    Write-Host "  poetry run uvicorn app.main:app --reload" -ForegroundColor Yellow
    Write-Host ""
    exit 1
}

Write-Host ""
Write-Host "Creating test data..." -ForegroundColor Cyan
Write-Host ""

# Create Project 1: The Lund Covenant
Write-Host "Creating project: The Lund Covenant..." -ForegroundColor Yellow
$project1 = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/projects" -Method POST -ContentType "application/json" -Body (@{
    title = "The Lund Covenant"
    description = "Literary fiction novel - submission and query phase"
    status = "active"
    priority = 1
} | ConvertTo-Json)

Write-Host "Created project ID: $($project1.id) - $($project1.title)" -ForegroundColor Green

# Create tasks for Project 1
Write-Host ""
Write-Host "Creating tasks for The Lund Covenant..." -ForegroundColor Yellow

$tasks1 = @(
    @{
        title = "Research 10 literary agents specializing in literary fiction"
        description = "Look for agents with recent sales in similar genre. Check QueryTracker and Publishers Marketplace."
        project_id = $project1.id
        is_next_action = $true
        context = "administrative"
        energy_level = "medium"
        estimated_minutes = 45
    },
    @{
        title = "Draft personalized query letter"
        description = "Write compelling hook, brief synopsis, and author bio. Keep under 250 words."
        project_id = $project1.id
        is_next_action = $true
        context = "creative"
        energy_level = "high"
        estimated_minutes = 90
    },
    @{
        title = "Prepare 3-chapter sample (first 50 pages)"
        description = "Polish opening chapters, check formatting, proofread carefully."
        project_id = $project1.id
        is_next_action = $false
        context = "creative"
        energy_level = "high"
        estimated_minutes = 180
    },
    @{
        title = "Update submission tracker spreadsheet"
        description = "Add new agents to tracking sheet with contact info and submission dates."
        project_id = $project1.id
        is_next_action = $false
        context = "administrative"
        energy_level = "low"
        estimated_minutes = 15
    }
)

foreach ($task in $tasks1) {
    $result = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/tasks" -Method POST -ContentType "application/json" -Body ($task | ConvertTo-Json)
    Write-Host "  Created: $($result.title)" -ForegroundColor Green
}

# Create Project 2: Ley-Lines Reboot
Write-Host ""
Write-Host "Creating project: Ley-Lines Reboot..." -ForegroundColor Yellow
$project2 = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/projects" -Method POST -ContentType "application/json" -Body (@{
    title = "Guardians of the Ley Lines - Phase IV"
    description = "Fantasy series reboot - working with editor Melanie Jarvis"
    status = "active"
    priority = 2
} | ConvertTo-Json)

Write-Host "Created project ID: $($project2.id) - $($project2.title)" -ForegroundColor Green

# Create tasks for Project 2
Write-Host ""
Write-Host "Creating tasks for Ley-Lines Reboot..." -ForegroundColor Yellow

$tasks2 = @(
    @{
        title = "Review editor feedback on Phase 1 manuscript"
        description = "Go through Melanies notes and create action items for revisions."
        project_id = $project2.id
        is_next_action = $true
        context = "creative"
        energy_level = "medium"
        estimated_minutes = 60
    },
    @{
        title = "Revise opening chapter based on feedback"
        description = "Strengthen character introduction and world-building in chapter 1."
        project_id = $project2.id
        is_next_action = $false
        context = "creative"
        energy_level = "high"
        estimated_minutes = 120
    },
    @{
        title = "Schedule next check-in with Melanie"
        description = "Email to coordinate next phase review meeting."
        project_id = $project2.id
        is_next_action = $true
        context = "administrative"
        energy_level = "low"
        estimated_minutes = 10
    }
)

foreach ($task in $tasks2) {
    $result = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/tasks" -Method POST -ContentType "application/json" -Body ($task | ConvertTo-Json)
    Write-Host "  Created: $($result.title)" -ForegroundColor Green
}

# Create Project 3: Genealogy Project
Write-Host ""
Write-Host "Creating project: Operation Granny Files..." -ForegroundColor Yellow
$project3 = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/projects" -Method POST -ContentType "application/json" -Body (@{
    title = "Operation Granny Files - Mission 10"
    description = "Genealogy research and multimedia storytelling project"
    status = "active"
    priority = 3
} | ConvertTo-Json)

Write-Host "Created project ID: $($project3.id) - $($project3.title)" -ForegroundColor Green

# Create tasks for Project 3
Write-Host ""
Write-Host "Creating tasks for Operation Granny Files..." -ForegroundColor Yellow

$tasks3 = @(
    @{
        title = "Digitize old family photos from storage box"
        description = "Scan 50-100 photos from grandmothers collection. 300 DPI minimum."
        project_id = $project3.id
        is_next_action = $true
        context = "home"
        energy_level = "low"
        estimated_minutes = 90
    },
    @{
        title = "Research Lund family immigration records"
        description = "Search Ellis Island and Swedish emigration databases for 1890s records."
        project_id = $project3.id
        is_next_action = $false
        context = "research"
        energy_level = "medium"
        estimated_minutes = 60
    }
)

foreach ($task in $tasks3) {
    $result = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/tasks" -Method POST -ContentType "application/json" -Body ($task | ConvertTo-Json)
    Write-Host "  Created: $($result.title)" -ForegroundColor Green
}

# Create one completed project to show variety
Write-Host ""
Write-Host "Creating completed project: Winter Fire, Summer Ash..." -ForegroundColor Yellow
$project4 = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/projects" -Method POST -ContentType "application/json" -Body (@{
    title = "Winter Fire, Summer Ash - Story Bible"
    description = "Initial world-building and character development - COMPLETED"
    status = "completed"
    priority = 2
} | ConvertTo-Json)

Write-Host "Created project ID: $($project4.id) - $($project4.title)" -ForegroundColor Green

# Update momentum scores
Write-Host ""
Write-Host "Updating momentum scores..." -ForegroundColor Yellow
try {
    $momentum = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/intelligence/momentum/update" -Method POST -ErrorAction Stop
    Write-Host "Momentum scores updated" -ForegroundColor Green
    Write-Host "  Projects analyzed: $($momentum.projects_updated)" -ForegroundColor Cyan
} catch {
    Write-Host "Could not update momentum scores" -ForegroundColor Red
}

# Summary
Write-Host ""
Write-Host "================================" -ForegroundColor Cyan
Write-Host "Test Data Created Successfully!" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Summary:" -ForegroundColor Cyan
Write-Host "  4 Projects created" -ForegroundColor White
Write-Host "  9 Tasks created" -ForegroundColor White
Write-Host "  5 Next Actions defined" -ForegroundColor White
Write-Host "  Momentum scores calculated" -ForegroundColor White

Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "  1. Open your browser to: http://localhost:5173" -ForegroundColor White
Write-Host "  2. Explore the Dashboard to see your projects" -ForegroundColor White
Write-Host "  3. Check Next Actions for prioritized tasks" -ForegroundColor White
Write-Host "  4. Try filtering projects and next actions" -ForegroundColor White
Write-Host "  5. Use the Weekly Review page to see project health" -ForegroundColor White
Write-Host ""

Write-Host "Enjoy Conduital!" -ForegroundColor Green
Write-Host ""
