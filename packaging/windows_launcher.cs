// Pre-interpreter launcher: old updaters can carry a deleted PyInstaller _MEI
// environment. Reset it before loading the embedded, unchanged Python core.
using System;
using System.Collections;
using System.Diagnostics;
using System.IO;
using System.Reflection;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.Text;
using System.Windows.Forms;

[assembly: AssemblyTitle("RL Presence")]
[assembly: AssemblyDescription("Rocket League Discord Rich Presence")]
[assembly: AssemblyCompany("schwairex")]
[assembly: AssemblyProduct("RL Presence")]
[assembly: AssemblyVersion("@@VERSION@@.0")]
[assembly: AssemblyFileVersion("@@VERSION@@.0")]

internal static class Launcher {
    private const string CoreHash = "@@CORE_SHA256@@";
    [DllImport("kernel32.dll",CharSet=CharSet.Unicode)]
    private static extern bool SetDllDirectory(string path);

    private static string HashFile(string path) {
        using (var sha=SHA256.Create())
        using (var file=File.OpenRead(path))
            return BitConverter.ToString(sha.ComputeHash(file)).Replace("-","").ToLowerInvariant();
    }
    private static string ExtractCore() {
        string folder=Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),"RL Presence","runtime",CoreHash);
        Directory.CreateDirectory(folder);
        string target=Path.Combine(folder,"rl-presence-core.exe");
        if (File.Exists(target) && HashFile(target)==CoreHash) return target;
        string temporary=Path.Combine(folder,Guid.NewGuid().ToString("N")+".tmp");
        try {
            using (var resource=Assembly.GetExecutingAssembly().GetManifestResourceStream("rl-presence-core"))
            using (var file=new FileStream(temporary,FileMode.CreateNew,FileAccess.Write,FileShare.None)) {
                if(resource==null) throw new IOException("The application core is missing.");
                resource.CopyTo(file); file.Flush(true);
            }
            if(HashFile(temporary)!=CoreHash) throw new IOException("The application core checksum does not match.");
            if(File.Exists(target)) {
                // Another instance may have finished extraction in the meantime.
                if(HashFile(target)==CoreHash) return target;
                File.Delete(target); // only the exact verified cache file, never a tree
            }
            try { File.Move(temporary,target); }
            catch(IOException) { if(!File.Exists(target) || HashFile(target)!=CoreHash) throw; }
            return target;
        } finally { if(File.Exists(temporary)) File.Delete(temporary); }
    }
    private static string Quote(string value) {
        var result=new StringBuilder("\""); int slashes=0;
        foreach(char c in value) {
            if(c=='\\') { slashes++; continue; }
            if(c=='\"') result.Append('\\',slashes*2+1).Append(c);
            else result.Append('\\',slashes).Append(c);
            slashes=0;
        }
        return result.Append('\\',slashes*2).Append('"').ToString();
    }
    [STAThread]
    private static int Main(string[] args) {
        try {
            string outer=Assembly.GetExecutingAssembly().Location;
            string core=ExtractCore();
            var start=new ProcessStartInfo(core) { UseShellExecute=false,CreateNoWindow=true,WorkingDirectory=Environment.CurrentDirectory };
            var arguments=new StringBuilder();
            foreach(string arg in args) { if(arguments.Length>0)arguments.Append(' ');arguments.Append(Quote(arg)); }
            start.Arguments=arguments.ToString();
            foreach(DictionaryEntry item in Environment.GetEnvironmentVariables()) {
                string key=(string)item.Key;
                if(key.StartsWith("_PYI_",StringComparison.OrdinalIgnoreCase) || key.Equals("_MEIPASS2",StringComparison.OrdinalIgnoreCase) || key.StartsWith("RL_PRESENCE_LAUNCHER_",StringComparison.OrdinalIgnoreCase))
                    start.EnvironmentVariables.Remove(key);
            }
            start.EnvironmentVariables["PYINSTALLER_RESET_ENVIRONMENT"]="1";
            start.EnvironmentVariables["RL_PRESENCE_LAUNCHER_PATH"]=outer;
            start.EnvironmentVariables["RL_PRESENCE_LAUNCHER_PID"]=Process.GetCurrentProcess().Id.ToString();
            SetDllDirectory(null);
            using(var child=Process.Start(start)) { child.WaitForExit(); return child.ExitCode; }
        } catch(Exception error) {
            MessageBox.Show("RL Presence could not start. Please use a writable folder and check the .NET Framework 4.8 / WebView2 installation.\n\n"+error.Message,"RL Presence",MessageBoxButtons.OK,MessageBoxIcon.Error);
            return 1;
        }
    }
}
