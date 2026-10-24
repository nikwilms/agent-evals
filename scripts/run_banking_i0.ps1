<#
Run AgentDojo banking, injection task 0, with the important_instructions attack.
.EXAMPLE
  .\scripts\run_banking_i0.ps1 -Model groq/qwen/qwen3.8-27b
  .\scripts\run_banking_i0.ps1 -Model groq/openai/gpt-oss-20b -Epochs 5 -UserTasks "[3,5,6]"
#>
param(
    [Parameter(Mandatory)][string]$Model,
    [int]$Epochs = 1,
    [string]$UserTasks = ""
)
$args2 = @('eval', 'inspect_evals/agentdojo', '--model', $Model,
  '-T', 'workspace=banking', '-T', 'injection_task_ids=[0]',
  '--epochs', $Epochs, '--max-connections', '1',
  '--retry-on-error', '3', '--no-fail-on-error')
if ($UserTasks) { $args2 += @('-T', "user_task_ids=$UserTasks") }
& inspect @args2
