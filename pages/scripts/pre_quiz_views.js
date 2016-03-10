(function(root, _, Backbone){
  app = root.app || {};

  app.RejectionView = Backbone.View.extend({
    render: function(){
      this.$el.html(this.template());
      return this;
    }
  });

  app.RejectionTooEarlyView = app.RejectionView.extend({
    template: _.template($('#tpl_too_early').html())
  });

  app.RejectionTooLateView = app.RejectionView.extend({
    template: _.template($('#tpl_too_late').html())
  });

  app.RejectionNoMoreChanceView = app.RejectionView.extend({
    template: _.template($('#tpl_no_more_chance').html())
  });

  app.WelcomeView = Backbone.View.extend({
    tagName: 'div',
    className: 'welcome',
    template: _.template($('#tpl_welcome').html()),
    events: {
      'click .submit': 'onSubmit',
    },
    initialize: function(options){
      this.content = options.content;
      this.infoFields = options.infoFields;
      this.quizId = options.quizId;
    },
    render: function(){
      this.$el.html(this.template({
        content: this.content,
        infoFields: this.infoFields
      }));
      return this;
    },
    onSubmit: function(e){
      var field_keys = _.unzip(this.infoFields)[0];
      var validated = false;
      var field_data = [];
      if (field_keys.length){
        validated = _(this.$('input')).chain()
        .filter(function(input){
          return _(field_keys).indexOf(input.name) >= 0;
        }).every(function(input){
          if (input.value.length > 0){
            field_data.push([input.name, input.value])
            localStorage.setItem(input.name, input.value);
            return true;
          }
          return false;
        }).value();
      } else {
        validated = true;
      }
      if(validated){
        this.trigger('startQuiz', field_data);
      } else {
        app.modal({
          message: "亲，需填完信息才能开始哦~",
          emotion: "tricky",
          button: { text: "关闭" }
        });
      }
    }
  });

  root.app = app;
  return app;
})(this, _, Backbone);
