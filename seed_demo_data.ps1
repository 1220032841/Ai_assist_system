Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "  Seed Demo Users and C++ Assignment" -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host ""

Set-Location -Path $PSScriptRoot

$users = @(
    @{ email = "admin@example.com"; password = "admin123"; full_name = "Admin User"; role = "admin"; is_active = $true },
    @{ email = "teacher1@teacher.com"; password = "teacher123"; full_name = "Course Teacher"; role = "instructor"; is_active = $true },
    @{ email = "student1@student.com"; password = "student123"; full_name = "Student One"; role = "student"; is_active = $true },
    @{ email = "student2@student.com"; password = "student123"; full_name = "Student Two"; role = "student"; is_active = $true },
    @{ email = "student3@student.com"; password = "student123"; full_name = "Student Three"; role = "student"; is_active = $true },
    @{ email = "student4@student.com"; password = "student123"; full_name = "Student Four"; role = "student"; is_active = $true },
    @{ email = "student5@student.com"; password = "student123"; full_name = "Student Five"; role = "student"; is_active = $true }
)

Write-Host "[1/2] Seeding demo users..." -ForegroundColor Green
foreach ($u in $users) {
    $body = $u | ConvertTo-Json
    try {
        Invoke-RestMethod -Method Post -Uri "http://127.0.0.1/api/v1/users/" -ContentType "application/json" -Body $body | Out-Null
        Write-Host "[CREATED] $($u.email)" -ForegroundColor Green
    }
    catch {
        $msg = $_.ErrorDetails.Message
        if ($msg -and $msg -match "already exists") {
            Write-Host "[EXISTS ] $($u.email)" -ForegroundColor Yellow
        }
        else {
            Write-Host "[FAILED ] $($u.email)" -ForegroundColor Red
            if ($msg) {
                Write-Host $msg -ForegroundColor DarkRed
            }
        }
    }
}

Write-Host "" 
Write-Host "[2/2] Seeding 1 C++ assignment..." -ForegroundColor Green
& "$PSScriptRoot\seed_assignment.bat"
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] seed_assignment.bat failed." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "[OK] Demo data ready." -ForegroundColor Green
Write-Host "Teacher: teacher1@teacher.com / teacher123" -ForegroundColor Cyan
Write-Host "Students: student1..student5@student.com / student123" -ForegroundColor Cyan
