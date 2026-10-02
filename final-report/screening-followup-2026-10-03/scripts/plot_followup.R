# Figures use completed aggregate results only. No models are fitted here.
library(data.table)
library(ggplot2)
summary <- fread('outputs/screening_summary.csv')
pairs <- fread('outputs/paired_screening_summary.csv')
dir.create('figures', showWarnings = FALSE)
ink <- '#173C36'; teal <- '#237E72'; rust <- '#BD5A32'; grey <- '#A6B5AE'
base_theme <- theme_minimal(base_family = 'Arial', base_size = 12) +
 theme(plot.title = element_text(face='bold', colour=ink, size=20, margin=margin(b=9)),
       plot.subtitle = element_text(colour='#58665F', margin=margin(b=18)),
       plot.caption = element_text(hjust=0, colour='#58665F', size=9.5, margin=margin(t=16)),
       panel.grid.minor=element_blank(), panel.grid.major.x=element_blank(),
       panel.grid.major.y=element_line(colour='#E2E7E3'), axis.title.x=element_text(margin=margin(t=10)),
       axis.title.y=element_text(margin=margin(r=10)), strip.text=element_text(face='bold', colour=ink, size=12),
       plot.margin=margin(18,22,16,18), legend.position='bottom', legend.title=element_blank())
x <- summary[fraction == .25 & metric == 'precision']
x[, model := factor(model, levels=c('baseline','property_only','full'),
 labels=c('Group rate','Property\ninformation','Full\nmodel'))]
x[, scope := factor(scope, levels=c('all_eligible','priority_pool','priority_fixed_quota'),
 labels=c('All eligible homes','Three groups combined','Fixed quota in each group'))]
p1 <- ggplot(x,aes(x=model,y=mean,fill=model)) + geom_col(width=.62) +
 geom_text(aes(label=sprintf('%.1f%%',100*mean)),vjust=-.55,size=4.3,colour=ink,fontface='bold') +
 facet_wrap(~scope,nrow=1) + scale_fill_manual(values=c(grey,rust,teal)) +
 scale_y_continuous(labels=function(v)paste0(round(v*100),'%'),limits=c(0,max(x$mean)+.085),expand=expansion(mult=c(0,0))) +
 labs(title='Which information improves the shortlist?',
 subtitle='Select 25% of candidates. Every comparison uses the same test homes and allocation rule.',
 x=NULL,y='Selected homes reaching 30 reviews',
 caption='Equal-weight mean over 50 reused host splits. Fixed group quotas round up separately.\nHistorical, exploratory results. Reviews do not measure profit. Source: outputs/screening_summary.csv.') +
 base_theme + theme(legend.position='none')
ggsave('figures/model_comparison.png',p1,width=11.5,height=5.8,dpi=250,bg='white')
ggsave('figures/model_comparison.svg',p1,width=11.5,height=5.8,device=grDevices::svg,bg='white')
y <- pairs[scope=='priority_fixed_quota' & metric=='precision_difference_pp' & pair %in% c('full_vs_baseline','property_only_vs_baseline')]
y[, method := factor(pair,levels=c('property_only_vs_baseline','full_vs_baseline'),labels=c('Property information vs group rate','Full model vs group rate'))]
y[, quota := factor(fraction,levels=c(.1,.25,.5),labels=c('10%','25%','50%'))]
p2 <- ggplot(y,aes(x=quota,y=mean_difference,group=method,colour=method)) +
 geom_hline(yintercept=0,colour='#87958F',linetype='dashed') +
 geom_errorbar(aes(ymin=p05_difference,ymax=p95_difference),position=position_dodge(width=.22),width=.10,linewidth=.7) +
 geom_line(position=position_dodge(width=.22),linewidth=.8) +
 geom_point(position=position_dodge(width=.22),size=3.2) +
 scale_colour_manual(values=c(rust,teal)) +
 labs(title='Does the gain survive a change in shortlist size?',
 subtitle='The three priority groups, with the same quota fixed inside each group',
 x='Nominal share selected from each group',y='Extra target-reaching homes per 100 selected',
 caption='Points show mean paired gains over 50 host splits. Bars show the 5th to 95th percentiles, not confidence intervals.\nSplits overlap. Small rounded quotas can make individual group results unstable. Source: outputs/paired_screening_summary.csv.') +
 base_theme
ggsave('figures/quota_sensitivity.png',p2,width=10.5,height=6.3,dpi=250,bg='white')
ggsave('figures/quota_sensitivity.svg',p2,width=10.5,height=6.3,device=grDevices::svg,bg='white')
cat('Saved model comparison and quota sensitivity figures.\n')
