(function () {
  var rules = {
    register: function (f) {
      var e = {}, v = function (n) { return f.elements[n].value; };
      if (!v('name').trim()) e.name = 'Name is required';
      if (!v('email').trim()) e.email = 'Email is required';
      if (!v('password')) e.password = 'Password is required';
      if (!v('confirm_password')) e.confirm_password = 'Confirm password is required';
      else if (v('password') && v('password') !== v('confirm_password')) e.confirm_password = 'Passwords do not match';
      return e;
    },
    login: function (f) {
      var e = {};
      if (!f.elements.email.value.trim()) e.email = 'Email is required';
      if (!f.elements.password.value) e.password = 'Password is required';
      return e;
    },
    todo: function (f) {
      var e = {}, t = f.elements.title.value.trim();
      if (!t) e.title = 'Title is required';
      else if (t.length > 200) e.title = 'Title is too long (200 characters at most)';
      return e;
    }
  };

  document.querySelectorAll('form[data-validate]').forEach(function (form) {
    form.addEventListener('submit', function (ev) {
      var errs = rules[form.dataset.validate](form);
      form.querySelectorAll('[data-error-for]').forEach(function (box) {
        var name = box.dataset.errorFor;
        box.textContent = errs[name] || '';
        var input = form.elements[name];
        if (input) input.classList.toggle('invalid', !!errs[name]);
      });
      if (Object.keys(errs).length) ev.preventDefault();
    });
  });

  document.querySelectorAll('form[data-confirm]').forEach(function (form) {
    form.addEventListener('submit', function (ev) {
      if (!window.confirm(form.dataset.confirm)) ev.preventDefault();
    });
  });
})();
