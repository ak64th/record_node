(function(root, $, _, Backbone){
  app = root.app || {};

  app.ModalView = Backbone.View.extend({
    tagName: 'div',
    className: 'modal',
    template: _.template($('#tpl_modal').html()),
    events: {
      'click .submit': 'close'
    },
    initialize: function(options){
      this.options = options;
      this.callback = options.callback;
    },
    render: function(){
      this.$el.html(this.template(this.options));
      return this;
    },
    close: function(){
      _.isFunction(this.callback) && this.callback();
      this.remove();
    }
  });

  app.modal = function(options){
    var view = new app.ModalView(options);
    $('body').append(view.render().el);
  };

  root.app = app;
  return app;
})(window, $, _, Backbone);
