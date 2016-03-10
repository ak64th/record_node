(function(root, _, Backbone){
  app = root.app || {};

  app.RankView = Backbone.View.extend({
    tagName: 'div',
    className: 'rank',
    template: _.template($('#tpl_rank').html()),
    events: {'click .submit': 'onSubmit'},
    initialize: function(options) {
      console.log(options);
      this.result = options.result;
    },
    render: function(){
      this.$el.html(this.template(this.result));
      return this;
    },
    onSubmit: function(){
      this.trigger('rerun');
    }
  });

  root.app = app;
  return app;
})(this, _, Backbone);
