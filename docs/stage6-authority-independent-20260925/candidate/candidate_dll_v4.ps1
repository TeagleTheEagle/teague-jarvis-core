# Candidate-local native bridge. No process creation occurs in EnsureLoaded.
function Initialize-J6CandidateBridge {
 $dll=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot 'J6OwnedEntry.dll'))
 if([IO.Path]::GetDirectoryName($dll) -cne $PSScriptRoot){throw 'DLL containment'}
 $item=Get-Item -LiteralPath $dll -ErrorAction Stop
 while($null -ne $item){if($item.Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'DLL reparse'};$item=$item.Parent}
 $dllLock=[IO.File]::Open($dll,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read)
 try {
 if((Get-FileHash -LiteralPath $dll -Algorithm SHA256).Hash.ToLowerInvariant() -cne 'ff2454390795bb302cdb68990b7f52fc02db7efedb55d2bbd3dd2cbd0e1da7ef'){throw 'DLL hash'}
 Add-Type -TypeDefinition @'
using System;
using System.IO;
using System.Text;
using System.Runtime.InteropServices;
public static class J6SmallCollector {
 [DllImport("kernel32.dll", CharSet=CharSet.Unicode, SetLastError=true)] static extern uint GetModuleFileNameW(IntPtr h,StringBuilder b,uint size);
 [UnmanagedFunctionPointer(CallingConvention.Cdecl,CharSet=CharSet.Unicode)] delegate int Run([MarshalAs(UnmanagedType.LPWStr)] string root,[MarshalAs(UnmanagedType.LPWStr)] string mode);
 static IntPtr module; static Run run;
 public static string EnsureLoaded(string path) {
  if(module!=IntPtr.Zero)throw new InvalidOperationException("Already loaded");
  module=NativeLibrary.Load(path,typeof(J6SmallCollector).Assembly,DllImportSearchPath.UseDllDirectoryForDependencies|DllImportSearchPath.System32);
  var b=new StringBuilder(32768);var n=GetModuleFileNameW(module,b,32768);
  if(n==0||n>=32768||!String.Equals(Path.GetFullPath(path),b.ToString(),StringComparison.OrdinalIgnoreCase))throw new InvalidOperationException("Loaded module mismatch");
  run=Marshal.GetDelegateForFunctionPointer<Run>(NativeLibrary.GetExport(module,"RunCollector"));return b.ToString();
 }
 public static int RunCollector(string root,string mode) {if(run==null)throw new InvalidOperationException("Not verified");return run(root,mode);}
}
'@
 [void][J6SmallCollector]::EnsureLoaded($dll)
 } finally {$dllLock.Dispose()}
}
