
library('drc')

#data = read.table("../../sample_data/BIBF_k.txt", header=TRUE)
data = read.table("../../sample_data/Geldanamycin_k.txt", header=TRUE)


# a is the "scale"
# b is the "shape"
# c is the lower bound
# d is the upper bound
# e is the inflection point


drm(formula = data$response ~ data$dose, fct = LL.2())

# b:(Intercept)  e:(Intercept)
#        482.4       106836.6

drm(formula = data$response ~ data$dose, fct = LL.3())

# b:(Intercept)  d:(Intercept)  e:(Intercept)
#        2.297         77.984       2675.295

drm(formula = data$response ~ data$dose, fct = LL.4())

# b:(Intercept)  c:(Intercept)  d:(Intercept)  e:(Intercept)
#       2.2853        -0.3575        77.9966      2686.8896

drm(formula = data$response ~ data$dose, fct = LL.5())

# b:(Intercept)  c:(Intercept)  d:(Intercept)  e:(Intercept)  f:(Intercept)
#       3.8198       -25.3687        77.9136      1157.6146         0.1559

drm(formula = data$response ~ data$dose, fct = W1.2())

# b:(Intercept)  e:(Intercept)
#        246.4       357409.8

drm(formula = data$response ~ data$dose, fct = W1.3())

# b:(Intercept)  d:(Intercept)  e:(Intercept)
#        1.883         78.041       3379.393

drm(formula = data$response ~ data$dose, fct = W1.4())

# b:(Intercept)  c:(Intercept)  d:(Intercept)  e:(Intercept)
#        1.920          3.305         78.020       3246.037

drm(formula = data$response ~ data$dose, fct = W2.4())

# b:(Intercept)  c:(Intercept)  d:(Intercept)  e:(Intercept)
#       -1.190         -9.685         77.929       2148.887

#####################################################################

# Fixed points: estimates disappear!

drm(formula = data$response ~ data$dose, fct = W2.4(fixed = c(NA, 0, NA, NA)))

# b:(Intercept)  d:(Intercept)  e:(Intercept)
#       -1.465         77.817       1901.889

#####################################################################

model = drm(formula = data$response ~ data$dose, fct = W2.4())

model.summ = summary(model)

# Model fitted: Weibull (type 2) (4 parms)
#
# Parameter estimates:
#
#                 Estimate Std. Error    t-value p-value
# b:(Intercept)   -1.19024    0.41770   -2.84954  0.0051
# c:(Intercept)   -9.68458   15.35835   -0.63057  0.5295
# d:(Intercept)   77.92899    2.22659   34.99930  0.0000
# e:(Intercept) 2148.88725  496.34452    4.32943  0.0000
#
# Residual standard error:
#
#  19.8904 (124 degrees of freedom)

model$

# model$boxcox        model$curveVarNam   model$estMethod     model$origData      model$predres       model$summary
# model$call          model$data          model$fct           model$parNames      model$robust        model$type
# model$cm            model$dataList      model$fit           model$parmMat       model$scaleFct      model$varParm
# model$coefficients  model$deriv1        model$indexMat      model$pfFct         model$start         model$weights
# model$curve         model$df.residual   model$logDose       model$pmFct         model$sumList

model.summ$

# model.summ$boxcox        model.summ$df.residual   model.summ$resVar        model.summ$text          model.summ$varParm
# model.summ$coefficients  model.summ$fctName       model.summ$robust        model.summ$type
# model.summ$cov.unscaled  model.summ$noParm        model.summ$rseMat        model.summ$varMat

#######################################################################

plot(model, type="all", broken=FALSE, xlim=c(0, max(data$dose)), ylim=c(0,100), lty="dashed", lwd=1.3, cex.lab=1.2, cex.main=2, cex=2)
points(data$dose, fitted(model)[1:length(data$dose)], col='blue')
model$curve[[1]](seq(10000))



