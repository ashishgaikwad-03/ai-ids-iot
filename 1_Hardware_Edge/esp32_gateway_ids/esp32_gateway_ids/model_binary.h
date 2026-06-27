// Auto-generated hardware calculation logic matrix
// Generated via Kaggle production workspace configuration pipelines

#include <math.h>
#include <string.h>
double sigmoid(double x) {
    if (x < 0.0) {
        double z = exp(x);
        return z / (1.0 + z);
    }
    return 1.0 / (1.0 + exp(-x));
}
void score(double * input, double * output) {
    double var0;
    if (input[7] < -0.9777778) {
        if (input[11] < 0.22) {
            if (input[9] < 0.012345679) {
                var0 = -0.024615385;
            } else {
                var0 = -0.18274148;
            }
        } else {
            if (input[2] < -0.4175477) {
                var0 = -0.09189189;
            } else {
                var0 = 0.17101449;
            }
        }
    } else {
        var0 = 0.19997013;
    }
    double var1;
    if (input[7] < -0.9777778) {
        if (input[11] < 0.22) {
            if (input[9] < 0.13580246) {
                var1 = -0.067223825;
            } else {
                var1 = -0.16661483;
            }
        } else {
            if (input[2] < -0.4175477) {
                var1 = -0.083859555;
            } else {
                var1 = 0.15601294;
            }
        }
    } else {
        var1 = 0.1818481;
    }
    double var2;
    if (input[7] < -0.9777778) {
        if (input[10] < 0.31) {
            if (input[9] < 0.012345679) {
                var2 = 0.002969542;
            } else {
                var2 = -0.15273015;
            }
        } else {
            if (input[0] < 0.1904762) {
                var2 = 0.17232254;
            } else {
                var2 = 0.02697353;
            }
        }
    } else {
        var2 = 0.16823585;
    }
    double var3;
    if (input[7] < -0.9777778) {
        if (input[11] < 0.22) {
            if (input[2] < 1.1795704) {
                var3 = -0.14230502;
            } else {
                var3 = 0.011403493;
            }
        } else {
            if (input[2] < -0.41258273) {
                var3 = -0.044737514;
            } else {
                var3 = 0.15857004;
            }
        }
    } else {
        var3 = 0.15766649;
    }
    double var4;
    if (input[7] < -0.9777778) {
        if (input[10] < 0.31) {
            if (input[9] < 0.13580246) {
                var4 = -0.0285756;
            } else {
                var4 = -0.13428056;
            }
        } else {
            if (input[9] < 0.50617284) {
                var4 = 0.03200766;
            } else {
                var4 = 0.16336252;
            }
        }
    } else {
        var4 = 0.1492514;
    }
    double var5;
    if (input[7] < -0.9777778) {
        if (input[11] < 0.22) {
            if (input[5] < 2.931174) {
                var5 = -0.111748375;
            } else {
                var5 = -0.1395661;
            }
        } else {
            if (input[2] < -0.41258273) {
                var5 = -0.03247531;
            } else {
                var5 = 0.14884539;
            }
        }
    } else {
        var5 = 0.14241911;
    }
    double var6;
    if (input[7] < -0.9777778) {
        if (input[11] < 0.22) {
            if (input[2] < 2.4540827) {
                var6 = -0.11968314;
            } else {
                var6 = 0.036867432;
            }
        } else {
            if (input[2] < -0.4175477) {
                var6 = -0.049494326;
            } else {
                var6 = 0.127809;
            }
        }
    } else {
        var6 = 0.13678437;
    }
    double var7;
    if (input[7] < -0.9777778) {
        if (input[9] < 0.13580246) {
            if (input[2] < -0.41419825) {
                var7 = -0.07274041;
            } else {
                var7 = 0.15322678;
            }
        } else {
            if (input[10] < 0.31) {
                var7 = -0.11489673;
            } else {
                var7 = 0.15040694;
            }
        }
    } else {
        var7 = 0.13207765;
    }
    double var8;
    if (input[7] < -0.9777778) {
        if (input[5] < 2.931174) {
            if (input[3] < 2.3480327) {
                var8 = -0.09861645;
            } else {
                var8 = 0.051139366;
            }
        } else {
            if (input[4] < 0.11685291) {
                var8 = -0.099895276;
            } else {
                var8 = -0.126589;
            }
        }
    } else {
        var8 = 0.12810433;
    }
    double var9;
    if (input[7] < -0.9777778) {
        if (input[5] < 2.931174) {
            if (input[5] < 2.8906882) {
                var9 = -0.091228746;
            } else {
                var9 = 0.1032408;
            }
        } else {
            if (input[4] < 0.11685291) {
                var9 = -0.0951676;
            } else {
                var9 = -0.12247988;
            }
        }
    } else {
        var9 = 0.12472041;
    }
    double var10;
    if (input[7] < -0.9777778) {
        if (input[9] < 0.13580246) {
            if (input[2] < -0.41419825) {
                var10 = -0.05341148;
            } else {
                var10 = 0.14950724;
            }
        } else {
            if (input[10] < 0.21) {
                var10 = -0.10121512;
            } else {
                var10 = 0.124959126;
            }
        }
    } else {
        var10 = 0.12181672;
    }
    double var11;
    if (input[7] < -0.9777778) {
        if (input[5] < 2.931174) {
            if (input[3] < 2.3480327) {
                var11 = -0.084507994;
            } else {
                var11 = 0.05563437;
            }
        } else {
            if (input[4] < 0.11685291) {
                var11 = -0.086114876;
            } else {
                var11 = -0.11614442;
            }
        }
    } else {
        var11 = 0.11930913;
    }
    double var12;
    if (input[7] < -0.9777778) {
        if (input[11] < 0.12) {
            if (input[2] < 2.4540827) {
                var12 = -0.09394899;
            } else {
                var12 = 0.08414858;
            }
        } else {
            if (input[10] < 0.01) {
                var12 = -0.015719308;
            } else {
                var12 = 0.1628738;
            }
        }
    } else {
        var12 = 0.11713163;
    }
    double var13;
    if (input[7] < -0.9777778) {
        if (input[5] < 2.931174) {
            if (input[3] < 1.9431148) {
                var13 = -0.07652006;
            } else {
                var13 = 0.055454608;
            }
        } else {
            if (input[4] < 0.11685291) {
                var13 = -0.07774859;
            } else {
                var13 = -0.11103294;
            }
        }
    } else {
        var13 = 0.115231715;
    }
    double var14;
    if (input[7] < -0.9777778) {
        if (input[5] < 2.931174) {
            if (input[5] < 2.8906882) {
                var14 = -0.069734864;
            } else {
                var14 = 0.10785844;
            }
        } else {
            if (input[4] < 0.11685291) {
                var14 = -0.07402729;
            } else {
                var14 = -0.10856245;
            }
        }
    } else {
        var14 = 0.11356703;
    }
    double var15;
    if (input[7] < -0.9777778) {
        if (input[5] < 2.931174) {
            if (input[3] < 1.9431148) {
                var15 = -0.06892855;
            } else {
                var15 = 0.04837513;
            }
        } else {
            if (input[4] < 0.08811828) {
                var15 = -0.067049526;
            } else {
                var15 = -0.10590386;
            }
        }
    } else {
        var15 = 0.1121031;
    }
    double var16;
    if (input[7] < -0.9777778) {
        if (input[11] < 0.12) {
            if (input[4] < -0.02423507) {
                var16 = 0.105382025;
            } else {
                var16 = -0.08064332;
            }
        } else {
            if (input[10] < 0.01) {
                var16 = 0.006999933;
            } else {
                var16 = 0.16734405;
            }
        }
    } else {
        var16 = 0.110811494;
    }
    double var17;
    if (input[7] < -0.9777778) {
        if (input[9] < 0.13580246) {
            if (input[4] < 1.9634721) {
                var17 = 0.15602508;
            } else {
                var17 = -0.018620096;
            }
        } else {
            if (input[10] < 0.01) {
                var17 = -0.078669086;
            } else {
                var17 = 0.07162455;
            }
        }
    } else {
        var17 = 0.10966865;
    }
    double var18;
    if (input[7] < -0.9777778) {
        if (input[5] < 2.931174) {
            if (input[5] < 2.8906882) {
                var18 = -0.05479696;
            } else {
                var18 = 0.111012354;
            }
        } else {
            if (input[4] < 0.12879144) {
                var18 = -0.059392203;
            } else {
                var18 = -0.10120984;
            }
        }
    } else {
        var18 = 0.10865479;
    }
    double var19;
    if (input[7] < -0.9777778) {
        if (input[5] < 2.931174) {
            if (input[3] < 1.4831967) {
                var19 = -0.055881537;
            } else {
                var19 = 0.047013525;
            }
        } else {
            if (input[4] < 0.12879144) {
                var19 = -0.056136258;
            } else {
                var19 = -0.099289924;
            }
        }
    } else {
        var19 = 0.10775321;
    }
    double var20;
    if (input[7] < -0.9777778) {
        if (input[5] < 2.931174) {
            if (input[14] < 5.327225) {
                var20 = -0.020980077;
            } else {
                var20 = -0.08796061;
            }
        } else {
            if (input[4] < 0.11685291) {
                var20 = -0.0519867;
            } else {
                var20 = -0.09728155;
            }
        }
    } else {
        var20 = 0.10694975;
    }
    double var21;
    if (input[7] < -0.9777778) {
        if (input[5] < 2.931174) {
            if (input[3] < 1.9431148) {
                var21 = -0.048818134;
            } else {
                var21 = 0.05471909;
            }
        } else {
            if (input[4] < 0.12879144) {
                var21 = -0.049810868;
            } else {
                var21 = -0.09557607;
            }
        }
    } else {
        var21 = 0.10623232;
    }
    double var22;
    if (input[7] < -0.9777778) {
        if (input[11] < 0.12) {
            if (input[0] < -0.48809522) {
                var22 = 0.04567706;
            } else {
                var22 = -0.06510259;
            }
        } else {
            if (input[10] < 0.01) {
                var22 = 0.033858217;
            } else {
                var22 = 0.16392764;
            }
        }
    } else {
        var22 = 0.10559048;
    }
    double var23;
    if (input[7] < -0.9777778) {
        if (input[5] < 2.931174) {
            if (input[14] < 5.327225) {
                var23 = -0.0122480905;
            } else {
                var23 = -0.08142964;
            }
        } else {
            if (input[4] < 0.1867864) {
                var23 = -0.048050087;
            } else {
                var23 = -0.093543276;
            }
        }
    } else {
        var23 = 0.10501523;
    }
    double var24;
    if (input[7] < -0.9777778) {
        if (input[5] < 2.931174) {
            if (input[5] < 2.8906882) {
                var24 = -0.037515383;
            } else {
                var24 = 0.102648795;
            }
        } else {
            if (input[4] < 0.1867864) {
                var24 = -0.045144428;
            } else {
                var24 = -0.091762595;
            }
        }
    } else {
        var24 = 0.10449876;
    }
    double var25;
    if (input[7] < -0.9777778) {
        if (input[11] < 0.01) {
            if (input[2] < 2.4540827) {
                var25 = -0.061036486;
            } else {
                var25 = 0.14381735;
            }
        } else {
            if (input[9] < 0.75308645) {
                var25 = 0.060686715;
            } else {
                var25 = -0.03457911;
            }
        }
    } else {
        var25 = 0.10403426;
    }
    double var26;
    if (input[7] < -0.9777778) {
        if (input[5] < 2.931174) {
            if (input[14] < 5.327225) {
                var26 = -0.0052955383;
            } else {
                var26 = -0.075453006;
            }
        } else {
            if (input[4] < 0.1867864) {
                var26 = -0.038455505;
            } else {
                var26 = -0.088804916;
            }
        }
    } else {
        var26 = 0.10361576;
    }
    double var27;
    if (input[7] < -0.9777778) {
        if (input[10] < 0.01) {
            if (input[9] < 0.13580246) {
                var27 = 0.07224444;
            } else {
                var27 = -0.05116163;
            }
        } else {
            if (input[0] < 0.35714287) {
                var27 = 0.15323965;
            } else {
                var27 = 0.0053134756;
            }
        }
    } else {
        var27 = 0.103238;
    }
    double var28;
    if (input[7] < -0.9777778) {
        if (input[5] < 2.931174) {
            if (input[5] < 2.8906882) {
                var28 = -0.027689418;
            } else {
                var28 = 0.106333114;
            }
        } else {
            if (input[14] < -0.18979058) {
                var28 = 0.009644105;
            } else {
                var28 = -0.08106366;
            }
        }
    } else {
        var28 = 0.10289635;
    }
    double var29;
    if (input[7] < -0.9777778) {
        if (input[11] < 0.01) {
            if (input[4] < -0.02423507) {
                var29 = 0.13656336;
            } else {
                var29 = -0.051078916;
            }
        } else {
            if (input[9] < 0.75308645) {
                var29 = 0.061081834;
            } else {
                var29 = -0.024150996;
            }
        }
    } else {
        var29 = 0.1025867;
    }
    double var30;
    if (input[7] < -0.9777778) {
        if (input[5] < 2.931174) {
            if (input[3] < 1.4831967) {
                var30 = -0.028286343;
            } else {
                var30 = 0.06331112;
            }
        } else {
            if (input[4] < 0.1867864) {
                var30 = -0.022829408;
            } else {
                var30 = -0.08309488;
            }
        }
    } else {
        var30 = 0.102305405;
    }
    double var31;
    if (input[7] < -0.9777778) {
        if (input[9] < 0.6296296) {
            if (input[4] < 1.4935243) {
                var31 = 0.1496103;
            } else {
                var31 = -0.0055270377;
            }
        } else {
            if (input[2] < 2.694067) {
                var31 = -0.04922519;
            } else {
                var31 = 0.12527882;
            }
        }
    } else {
        var31 = 0.102049194;
    }
    double var32;
    if (input[7] < -0.9777778) {
        if (input[5] < 2.931174) {
            if (input[14] < 5.327225) {
                var32 = 0.005679078;
            } else {
                var32 = -0.06529868;
            }
        } else {
            if (input[4] < 0.12879144) {
                var32 = -0.009764993;
            } else {
                var32 = -0.0783112;
            }
        }
    } else {
        var32 = 0.10181513;
    }
    double var33;
    if (input[7] < -0.9777778) {
        if (input[10] < 0.01) {
            if (input[9] < 0.13580246) {
                var33 = 0.06574132;
            } else {
                var33 = -0.037317608;
            }
        } else {
            if (input[0] < 0.2595238) {
                var33 = 0.15012677;
            } else {
                var33 = 0.03322109;
            }
        }
    } else {
        var33 = 0.1016006;
    }
    double var34;
    if (input[7] < -0.9777778) {
        if (input[11] < 0.01) {
            if (input[14] < -0.09816754) {
                var34 = 0.03948495;
            } else {
                var34 = -0.044331443;
            }
        } else {
            if (input[4] < 14.112465) {
                var34 = 0.020281266;
            } else {
                var34 = 0.18102825;
            }
        }
    } else {
        var34 = 0.10140319;
    }
    double var35;
    if (input[7] < -0.9777778) {
        if (input[5] < 2.931174) {
            if (input[5] < 2.8906882) {
                var35 = -0.015391353;
            } else {
                var35 = 0.10552204;
            }
        } else {
            if (input[4] < 0.1867864) {
                var35 = -0.008525466;
            } else {
                var35 = -0.07593345;
            }
        }
    } else {
        var35 = 0.10122075;
    }
    double var36;
    if (input[7] < -0.9777778) {
        if (input[11] < 0.01) {
            if (input[4] < 0.08811828) {
                var36 = 0.03626075;
            } else {
                var36 = -0.0415292;
            }
        } else {
            if (input[0] < 0.2595238) {
                var36 = 0.06319681;
            } else {
                var36 = -0.0060134106;
            }
        }
    } else {
        var36 = 0.10105131;
    }
    double var37;
    if (input[7] < -0.9777778) {
        if (input[5] < 2.931174) {
            if (input[3] < 7.055328) {
                var37 = -0.010444914;
            } else {
                var37 = 0.14557809;
            }
        } else {
            if (input[14] < -0.18979058) {
                var37 = 0.047163595;
            } else {
                var37 = -0.06592122;
            }
        }
    } else {
        var37 = 0.10089304;
    }
    double var38;
    if (input[7] < -0.9777778) {
        if (input[10] < 0.01) {
            if (input[12] < 0.12) {
                var38 = -0.026308674;
            } else {
                var38 = 0.12417068;
            }
        } else {
            if (input[14] < -0.018324608) {
                var38 = -0.016711278;
            } else {
                var38 = 0.12318715;
            }
        }
    } else {
        var38 = 0.10074427;
    }
    double var39;
    if (input[7] < -0.9777778) {
        if (input[9] < 0.6296296) {
            if (input[4] < 12.803955) {
                var39 = 0.008397973;
            } else {
                var39 = 0.17812082;
            }
        } else {
            if (input[2] < 2.694067) {
                var39 = -0.034302466;
            } else {
                var39 = 0.12067193;
            }
        }
    } else {
        var39 = 0.100603454;
    }
    double var40;
    var40 = sigmoid(var0 + var1 + var2 + var3 + var4 + var5 + var6 + var7 + var8 + var9 + var10 + var11 + var12 + var13 + var14 + var15 + var16 + var17 + var18 + var19 + var20 + var21 + var22 + var23 + var24 + var25 + var26 + var27 + var28 + var29 + var30 + var31 + var32 + var33 + var34 + var35 + var36 + var37 + var38 + var39);
    memcpy(output, (double[]){1.0 - var40, var40}, 2 * sizeof(double));
}
