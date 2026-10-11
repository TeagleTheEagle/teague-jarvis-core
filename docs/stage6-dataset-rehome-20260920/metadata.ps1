param([ValidateSet('before','after')][string]$Phase)
$ErrorActionPreference='Stop'
$plan=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'copy-result.json') -Raw|ConvertFrom-Json
$source='D:\JARVIS-STAGE6-LIVE\1c1f5d0c390b42cc9ba9f4f6221dabc6\code\large-synthetic'
$target='D:\JARVIS-STAGE6-LIVE\e23d36c0a24246c996aa28e5d5561863\code\large-synthetic'
if($plan.source -cne $source -or $plan.destination -cne $target){throw 'Unexpected synthetic roots'}
$all=@{}
foreach($entry in @(@('old',$source),@('new',$target))){
 $root=$entry[1];$items=@(Get-Item -LiteralPath $root)+@(Get-ChildItem -LiteralPath $root -Recurse -Force)
 $rows=@(foreach($p in $items){
  if($p.Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Reparse metadata refused'}
  $acl=Get-Acl -LiteralPath $p.FullName
  [pscustomobject]@{path=$p.FullName;directory=$p.PSIsContainer;attributes=[int]$p.Attributes;creationUtc=$p.CreationTimeUtc.ToString('o');lastWriteUtc=$p.LastWriteTimeUtc.ToString('o');sddl=$acl.Sddl}
 })
 $all[$entry[0]]=$rows
}
$dest=Join-Path $PSScriptRoot ('metadata-'+$Phase+'.json')
if(Test-Path -LiteralPath $dest){throw 'Preserved metadata exists'}
$all|ConvertTo-Json -Depth 8|Set-Content -LiteralPath $dest
@{phase=$Phase;oldEntries=$all.old.Count;newEntries=$all.new.Count}|ConvertTo-Json
