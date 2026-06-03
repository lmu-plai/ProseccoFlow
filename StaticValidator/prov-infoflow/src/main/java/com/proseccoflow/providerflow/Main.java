package com.proseccoflow.providerflow;

import soot.SootMethod;
import soot.jimple.infoflow.InfoflowConfiguration;
import soot.jimple.infoflow.InfoflowManager;
import soot.jimple.infoflow.android.InfoflowAndroidConfiguration;
import soot.jimple.infoflow.android.SetupApplication;
import soot.jimple.infoflow.collections.codeOptimization.ConstantTagFolding;
import soot.jimple.infoflow.collections.codeOptimization.StringResourcesResolver;
import soot.jimple.infoflow.methodSummary.data.provider.EagerSummaryProvider;
import soot.jimple.infoflow.methodSummary.taintWrappers.SummaryTaintWrapper;

import java.io.*;
import java.net.URISyntaxException;
import java.nio.file.Files;
import java.util.Collections;
import java.util.Set;

/*
Method for defining the configuration, executing the static data flow analysis and processing the results of FlowDroid
 */
public class Main {
    public static void main(String[] args) {
        File pathAndroid = new File ("../../Library/Android/sdk/platforms");
        File pathAPK = new File("../../APKs/case studies");
        File[] apks = pathAPK.listFiles((dir, name) -> name.toLowerCase().endsWith(".apk"));
        File sourceSinkFile = new File("SourcesSinks/SuSi_CoDoC.xml");
        File results_log;
        if (apks != null) {
            for (File apk : apks) {
                results_log = new File("Log.log");
                SetupApplication app = new SetupApplication(pathAndroid, apk);
                //SetupApplication app = new SetupApplication(pathAndroid, pathAPK);
                try {
                    app.setTaintWrapper(new SummaryTaintWrapper(new EagerSummaryProvider("summariesManual")));
                } catch (IOException | URISyntaxException e) {
                    continue;
                }
                //app.setTaintPropagationHandler(new DebugFlowFunctionTaintPropagationHandler());

                InfoflowConfiguration conf = app.getConfig();
                conf.getPathConfiguration().setPathReconstructionTimeout(900);
                conf.setDataFlowTimeout(900);
                //conf.setWriteOutputFiles(true);
                app.addOptimizationPass(new SetupApplication.OptimizationPass() {
                    @Override
                    public void performCodeInstrumentationBeforeDCE(InfoflowManager manager, Set<SootMethod> set) {
                        ConstantTagFolding ctf = new ConstantTagFolding();
                        ctf.initialize(manager.getConfig());
                        ctf.run(manager, Collections.emptySet(), manager.getSourceSinkManager(), manager.getTaintWrapper());

                        StringResourcesResolver res = new StringResourcesResolver(app);
                        res.initialize(manager.getConfig());
                        res.run(manager, Collections.emptySet(), manager.getSourceSinkManager(), manager.getTaintWrapper());
                    }

                    @Override
                    public void performCodeInstrumentationAfterDCE(InfoflowManager manager, Set<SootMethod> set) {

                    }
                });

                InfoflowAndroidConfiguration aconf = app.getConfig();
                aconf.setMergeDexFiles(true);
                aconf.getCallbackConfig().setCallbackAnalysisTimeout(900);

                try {
                    app.runInfoflow(sourceSinkFile);
                } catch (IOException e) {
                    continue;
                }

                File results_file = new File("../../Apps/Results/FlowDroid-Results/" + apk.getName() + ".txt");
                try {
                    Files.move(results_log.toPath(), results_file.toPath());
                } catch (IOException e) {
                    throw new RuntimeException(e);
                }
            }
        }
        System.exit(0);
    }
}